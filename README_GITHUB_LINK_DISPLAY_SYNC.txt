VIDEHA — GitHub Link Display Sync Fix
Date: 2026-08-21

Purpose:
Navigation was already correct, but on GitHub-hosted Videha pages the visible .vus-url text could still show:
  /videha/videha-quiz/...
while the actual anchor opened:
  https://videha-ejournal.github.io/videha-quiz/...

This update makes the global GitHub link guard also synchronize the visible .vus-url text
with the canonicalized href.

Upload the same contents to:
1. videha-ejournal/videha repository root
2. Videha primary server httpdocs root

No routing logic is changed beyond display synchronization.
