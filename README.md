# AIOS v0.8.1 — Responsive UI Layout

This release keeps the working AIOS v0.8 functionality and fixes desktop layout/clipping.

## UI improvements
- Responsive central workspace with vertical scrolling when needed
- Compact, consistent spacing and margins
- Two-column workspace cards instead of four squeezed cards
- Reduced hero and card sizing to fit common Windows resolutions better
- Sidebar width adapts between 160–190px
- AI command bar remains visible and accessible
- Taskbar remains anchored at the bottom
- File manager panel has a usable minimum height

## Run
```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

## Validation
27 tests passed; Python compilation passed.
