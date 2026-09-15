# Videha external preservation: Figshare + Dataverse

This integration publishes preservation/discovery records for the eight Videha repositories while keeping the existing Zenodo DOIs unchanged.

## Authoritative metadata

The workflow reads each repository's `.zenodo.json` at run time. The canonical creator is **Thakur, Gajendra**, resource type is **Dataset**, and repository-original/curatorial content is licensed **CC BY 4.0** subject to item-level rights notices.

The eight source repositories and their existing Zenodo DOIs are listed in `external-preservation-manifest.json`.

## Important identifier rule

Figshare and a Dataverse installation may mint their own persistent identifiers when records are published. Those identifiers are additional preservation/discovery identifiers. They do **not** replace or modify the existing Zenodo DOI. Each external record links back to the GitHub repository and the corresponding Zenodo DOI.

## One-time GitHub configuration

Open **Settings → Secrets and variables → Actions** in `videha-ejournal/videha`.

### Secrets

- `FIGSHARE_TOKEN` — Figshare personal/OAuth access token.
- `DATAVERSE_API_TOKEN` — API token from the chosen Dataverse installation.

### Variables

- `DATAVERSE_SERVER` — base URL of the chosen Dataverse installation, for example `https://<your-dataverse-host>`.
- `DATAVERSE_COLLECTION` — collection alias in which the datasets should be created; `root` is valid only if your account has Add Dataset permission there.
- `DATAVERSE_CONTACT_EMAIL` — dataset point-of-contact email required by Dataverse.
- `DATAVERSE_LICENSE_NAME` — set to `CC BY 4.0` if that licence is enabled by the chosen installation.
- `DATAVERSE_LICENSE_URI` — `https://creativecommons.org/licenses/by/4.0/`.
- `FIGSHARE_CATEGORY_IDS` — optional comma-separated category IDs. If omitted, the script attempts to select humanities/history/language/literature categories automatically.

Dataverse is software used by many separate repositories; there is no single universal Dataverse account or server. Choose the Dataverse installation in which these records are to be preserved before running the Dataverse part.

## Publishing workflow

Use **Actions → Publish Videha to Figshare and Dataverse → Run workflow**.

1. First run with `mode = draft`.
2. Review the eight draft records in Figshare and/or the chosen Dataverse installation.
3. Confirm creator, title, description, CC BY 4.0 licence, keywords, GitHub link, and Zenodo DOI relation.
4. Run again with `mode = publish`.

Provider IDs/PIDs returned by the APIs are written to `external-preservation-state.json`. This makes later runs update/reuse the same external records instead of intentionally creating a second set.

## Files

- `external-preservation-manifest.json` — eight repositories + existing Zenodo DOIs.
- `external-preservation-state.json` — provider IDs/PIDs returned after authenticated runs.
- `publish_external_archives.py` — API publisher.
- `.github/workflows/publish-figshare-dataverse.yml` — manual GitHub Actions entry point.

## Safety

The workflow is manual only. It never publishes merely because code is pushed. The default run mode is **draft**. Publication occurs only when `mode = publish` is explicitly selected.
