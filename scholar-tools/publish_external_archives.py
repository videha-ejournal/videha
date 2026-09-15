#!/usr/bin/env python3
"""Publish the eight Videha preservation datasets to Figshare and/or Dataverse.

The canonical descriptive metadata is read from each repository's .zenodo.json.
Existing Zenodo DOIs are preserved as related identifiers; this script never
changes them. Provider IDs/PIDs are stored in external-preservation-state.json
so reruns do not create duplicate records.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = BASE / "external-preservation-manifest.json"
DEFAULT_STATE = BASE / "external-preservation-state.json"
USER_AGENT = "Videha-Scholarly-Preservation/1.0 (+https://www.videha.co.in/)"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def http_json(method: str, url: str, headers=None, payload=None, timeout=45):
    headers = dict(headers or {})
    headers.setdefault("User-Agent", USER_AGENT)
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            parsed = None
            if raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    parsed = raw.decode("utf-8", errors="replace")
            return parsed, dict(response.headers.items()), response.status
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {detail[:1600]}") from exc


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_zenodo(repo_name: str):
    url = f"https://raw.githubusercontent.com/videha-ejournal/{repo_name}/main/.zenodo.json"
    data, _, _ = http_json("GET", url)
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid .zenodo.json for {repo_name}")
    return data


def preservation_description(meta, entry, manifest):
    doi_url = f"https://doi.org/{entry['zenodo_doi']}"
    base = meta.get("description", "").strip()
    rights = (
        "CC BY 4.0 applies to repository-original and curatorial metadata/dataset content; "
        "item-level authorship and rights notices prevail where applicable."
    )
    return (
        f"{base}\n\n"
        f"Source GitHub repository: {entry['github']}\n"
        f"Existing Zenodo archived-release DOI: {doi_url}\n"
        f"Parent publication: {manifest['publisher']} · ISSN {manifest['issn']} · {manifest['official_site']}\n"
        f"{rights}\n\n"
        "This Figshare/Dataverse record is an additional preservation and discovery record. "
        "It does not replace or alter the existing Zenodo DOI."
    )


def figshare_headers(token):
    return {"Authorization": f"token {token}"}


def pick_figshare_license(token):
    headers = figshare_headers(token)
    licenses, _, _ = http_json("GET", "https://api.figshare.com/v2/account/licenses", headers=headers)
    if not isinstance(licenses, list):
        licenses, _, _ = http_json("GET", "https://api.figshare.com/v2/licenses")
    for item in licenses or []:
        text = " ".join(str(item.get(k, "")) for k in ("name", "title", "url", "short_name")).lower()
        if "creativecommons.org/licenses/by/4.0" in text or "cc by 4.0" in text or "cc-by-4.0" in text:
            return int(item["id"])
    raise RuntimeError("Figshare account does not expose a recognizable CC BY 4.0 license")


def walk_category_objects(value):
    if isinstance(value, list):
        for item in value:
            yield from walk_category_objects(item)
    elif isinstance(value, dict):
        if "id" in value and any(k in value for k in ("title", "name")):
            yield value
        for child in value.values():
            if isinstance(child, (list, dict)):
                yield from walk_category_objects(child)


def pick_figshare_categories(token):
    configured = os.getenv("FIGSHARE_CATEGORY_IDS", "").strip()
    if configured:
        return [int(x.strip()) for x in configured.split(",") if x.strip()]
    categories, _, _ = http_json(
        "GET", "https://api.figshare.com/v2/account/categories", headers=figshare_headers(token)
    )
    wanted = ("arts and humanities", "humanities", "history", "language", "literature", "linguistics")
    picked = []
    for item in walk_category_objects(categories):
        label = str(item.get("title") or item.get("name") or "").lower()
        if any(term in label for term in wanted):
            cid = int(item["id"])
            if cid not in picked:
                picked.append(cid)
        if len(picked) >= 2:
            break
    return picked


def publish_figshare(entry, meta, manifest, state, do_publish):
    token = os.getenv("FIGSHARE_TOKEN", "").strip()
    if not token:
        raise RuntimeError("FIGSHARE_TOKEN is not configured")
    headers = figshare_headers(token)
    repo = entry["name"]
    existing = state.setdefault("figshare", {}).get(repo, {})
    article_id = existing.get("id")
    license_id = pick_figshare_license(token)
    categories = pick_figshare_categories(token)
    if do_publish and not categories:
        raise RuntimeError(
            "No suitable Figshare category was auto-detected. Set FIGSHARE_CATEGORY_IDS before publishing."
        )
    payload = {
        "title": meta.get("title") or repo,
        "description": preservation_description(meta, entry, manifest),
        "keywords": list(dict.fromkeys((meta.get("keywords") or []) + ["Videha", "Maithili"])),
        "references": [entry["github"], f"https://doi.org/{entry['zenodo_doi']}", manifest["official_site"]],
        "authors": [{"name": "Gajendra Thakur"}],
        "defined_type": "dataset",
        "license": license_id,
    }
    if categories:
        payload["categories"] = categories

    if article_id:
        http_json("PUT", f"https://api.figshare.com/v2/account/articles/{article_id}", headers, payload)
        action = "updated"
    else:
        created, response_headers, _ = http_json(
            "POST", "https://api.figshare.com/v2/account/articles", headers, payload
        )
        location = (created or {}).get("location") if isinstance(created, dict) else None
        location = location or response_headers.get("Location") or response_headers.get("location")
        if not location:
            raise RuntimeError(f"Figshare did not return a record location for {repo}")
        article_id = int(location.rstrip("/").split("/")[-1])
        # Add the immutable Zenodo release DOI as a linked resource.
        http_json(
            "POST",
            f"https://api.figshare.com/v2/account/articles/{article_id}/files",
            headers,
            {"link": f"https://doi.org/{entry['zenodo_doi']}"},
        )
        action = "created"

    if do_publish:
        http_json("POST", f"https://api.figshare.com/v2/account/articles/{article_id}/publish", headers)
        time.sleep(1)

    details, _, _ = http_json(
        "GET", f"https://api.figshare.com/v2/account/articles/{article_id}", headers=headers
    )
    record = {
        "id": article_id,
        "doi": (details or {}).get("doi") if isinstance(details, dict) else None,
        "url": (details or {}).get("url_public") if isinstance(details, dict) else None,
        "published": bool((details or {}).get("published_date")) if isinstance(details, dict) else do_publish,
        "zenodo_doi": entry["zenodo_doi"],
        "updated_at": now_iso(),
    }
    state["figshare"][repo] = record
    return {"provider": "figshare", "repository": repo, "action": action, **record}


def dv_field(type_name, type_class, multiple, value):
    return {"typeName": type_name, "typeClass": type_class, "multiple": multiple, "value": value}


def dataverse_payload(entry, meta, manifest, contact_email):
    description = preservation_description(meta, entry, manifest)
    author = {
        "authorName": dv_field("authorName", "primitive", False, "Thakur, Gajendra"),
        "authorAffiliation": dv_field(
            "authorAffiliation", "primitive", False, "Videha — First Maithili Fortnightly eJournal"
        ),
    }
    contact = {
        "datasetContactName": dv_field("datasetContactName", "primitive", False, "Gajendra Thakur"),
        "datasetContactAffiliation": dv_field(
            "datasetContactAffiliation", "primitive", False, "Videha — First Maithili Fortnightly eJournal"
        ),
        "datasetContactEmail": dv_field("datasetContactEmail", "primitive", False, contact_email),
    }
    desc = {"dsDescriptionValue": dv_field("dsDescriptionValue", "primitive", False, description)}
    fields = [
        dv_field("title", "primitive", False, meta.get("title") or entry["name"]),
        dv_field("author", "compound", True, [author]),
        dv_field("datasetContact", "compound", True, [contact]),
        dv_field("dsDescription", "compound", True, [desc]),
        dv_field("subject", "controlledVocabulary", True, ["Arts and Humanities"]),
    ]
    keywords = []
    for word in list(dict.fromkeys((meta.get("keywords") or []) + ["Videha", "Maithili"])):
        keywords.append({"keywordValue": dv_field("keywordValue", "primitive", False, word)})
    if keywords:
        fields.append(dv_field("keyword", "compound", True, keywords))

    return {
        "datasetVersion": {
            "license": {
                "name": os.getenv("DATAVERSE_LICENSE_NAME", "CC BY 4.0"),
                "uri": os.getenv(
                    "DATAVERSE_LICENSE_URI", "https://creativecommons.org/licenses/by/4.0/"
                ),
            },
            "metadataBlocks": {"citation": {"displayName": "Citation Metadata", "fields": fields}},
        }
    }


def publish_dataverse(entry, meta, manifest, state, do_publish):
    server = os.getenv("DATAVERSE_SERVER", "").strip().rstrip("/")
    token = os.getenv("DATAVERSE_API_TOKEN", "").strip()
    collection = os.getenv("DATAVERSE_COLLECTION", "root").strip() or "root"
    contact_email = os.getenv("DATAVERSE_CONTACT_EMAIL", "").strip()
    if not server:
        raise RuntimeError("DATAVERSE_SERVER is not configured")
    if not token:
        raise RuntimeError("DATAVERSE_API_TOKEN is not configured")
    if not contact_email:
        raise RuntimeError("DATAVERSE_CONTACT_EMAIL is required by Dataverse")
    headers = {"X-Dataverse-key": token}
    repo = entry["name"]
    existing = state.setdefault("dataverse", {}).get(repo, {})
    pid = existing.get("persistent_id")
    action = "existing"

    if not pid:
        payload = dataverse_payload(entry, meta, manifest, contact_email)
        created, _, _ = http_json(
            "POST",
            f"{server}/api/v1/dataverses/{urllib.parse.quote(collection, safe='')}/datasets",
            headers,
            payload,
        )
        data = (created or {}).get("data", {}) if isinstance(created, dict) else {}
        pid = data.get("persistentId") or data.get("persistent_id")
        if not pid:
            raise RuntimeError(f"Dataverse did not return a persistentId for {repo}: {created}")
        action = "created"
        state["dataverse"][repo] = {
            "persistent_id": pid,
            "url": f"{server}/dataset.xhtml?persistentId={urllib.parse.quote(pid)}",
            "published": False,
            "zenodo_doi": entry["zenodo_doi"],
            "updated_at": now_iso(),
        }
        save_json(DEFAULT_STATE, state)

    if do_publish and not state["dataverse"].get(repo, {}).get("published"):
        query = urllib.parse.urlencode({"persistentId": pid, "type": "major"})
        http_json(
            "POST", f"{server}/api/v1/datasets/:persistentId/actions/:publish?{query}", headers=headers
        )
        state["dataverse"][repo]["published"] = True
        action = "published" if action == "existing" else "created+published"

    state["dataverse"][repo].update({"updated_at": now_iso(), "zenodo_doi": entry["zenodo_doi"]})
    return {"provider": "dataverse", "repository": repo, "action": action, **state["dataverse"][repo]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("figshare", "dataverse", "both"), default="both")
    parser.add_argument("--publish", action="store_true", help="Publish instead of leaving provider records in draft")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--results", type=Path)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    state = load_json(args.state) if args.state.exists() else {"schema_version": 1, "figshare": {}, "dataverse": {}}
    state.setdefault("figshare", {})
    state.setdefault("dataverse", {})
    results = []
    failures = []

    for entry in manifest["repositories"]:
        repo = entry["name"]
        try:
            meta = load_zenodo(repo)
        except Exception as exc:
            failures.append({"repository": repo, "provider": "metadata", "error": str(exc)})
            continue

        providers = ("figshare", "dataverse") if args.provider == "both" else (args.provider,)
        for provider in providers:
            try:
                if provider == "figshare":
                    result = publish_figshare(entry, meta, manifest, state, args.publish)
                else:
                    result = publish_dataverse(entry, meta, manifest, state, args.publish)
                results.append(result)
                save_json(args.state, state)
                print(f"{provider}: {repo}: {result['action']}")
            except Exception as exc:
                failures.append({"repository": repo, "provider": provider, "error": str(exc)})
                print(f"ERROR {provider}: {repo}: {exc}", file=sys.stderr)

    output = {
        "generated_at": now_iso(),
        "mode": "publish" if args.publish else "draft",
        "provider": args.provider,
        "results": results,
        "failures": failures,
    }
    if args.results:
        args.results.parent.mkdir(parents=True, exist_ok=True)
        save_json(args.results, output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
