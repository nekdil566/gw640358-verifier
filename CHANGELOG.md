# Changelog

## v1.0 — Manual verifier (final)
- CSV and PDF import (PDF via local Flask backend `server.py`).
- Click-to-correct flow: row → fly to original → Edit → click map → red marker + deviation.
- OK / Reset / Undo (⌘/Ctrl+Z) per row; incremental table updates (no full rebuild).
- Live KPI box (OK / Review / Offset / Total).
- Auto-advance to next unverified turbine.
- Auto-save to localStorage; re-importable corrected-CSV export.
- Bundled Leaflet in `lib/` so it runs without internet for the UI shell.

## Earlier
- Classical-CV auto-verifier (`auto_verify.py`) — superseded; moved to the
  separate automated-detection repository.
