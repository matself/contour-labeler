# Contour Labeler

A QGIS plugin for placing slope-aligned elevation labels on contour lines, the way a
cartographer would: along a "ladder" you draw uphill across the contours.

Compatible with QGIS 3.34 up to 4.99 (Qt5 and Qt6).

## How it works

1. Open the **Contour Labeler** panel (toolbar icon or *Plugins* menu).
2. Choose the contour layer. The elevation field is guessed (`elev`, `z`, `height`, ...) and can be changed. The **Label font** button opens the full QGIS text format panel (font, size, colour, buffer) and updates the output layer live.
3. Click **Draw label ladder** and click uphill across the contours. Right-click or Enter finishes.
   Backspace removes the last point, Esc cancels.
4. A label is placed at every crossing. Its baseline follows the contour and the top of the
   text points uphill, whatever direction the contour was digitised in.
5. Not happy with the result? **Undo last ladder** (or Ctrl+Z while drawing) removes the labels
   from the last guide. Draw another one, as many as you like.

Labels go to a temporary layer called *Contour labels* with the fields `elev` and `rotation`,
already styled (rotated label with a white collar). **Save output…** exports it to a permanent
format, otherwise it is lost when the project is closed.

### Languages

The interface is English, with a Swedish translation that is used automatically when QGIS runs in Swedish. More languages: see `contour_labeler/i18n/README.md`.

### Options

- **Smoothing distance** (metres, default 5): how far each side of the crossing the contour
  direction is averaged. Increase it for jagged contours.

## Development

Link the plugin folder into your QGIS profile so changes are picked up (use the Plugin Reloader plugin):

```powershell
# Windows (run once, adjust profile name if needed)
New-Item -ItemType Junction `
  -Path "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\contour_labeler" `
  -Target "$PWD\contour_labeler"
```

Run the tests with the Python of an installed QGIS (`python-qgis.bat -m pytest`) and build an installable zip:

```bash
python scripts/build_zip.py   # -> dist/contour_labeler-0.1.0.zip
```

Code layout: `core.py` (label geometry, no GUI), `output.py` (output layer),
`maptool.py` (guide drawing tool), `dockwidget.py` (panel), `compat.py` (Qt5/Qt6 shims).

## Qt5 / Qt6 compatibility rules

- Import Qt only via `qgis.PyQt`, never `PyQt5` / `PyQt6`.
- Use fully scoped enums (`Qt.DockWidgetArea.RightDockWidgetArea`).
- Use `exec()`, not `exec_()`.
- Put anything that differs between QGIS 3 and 4 in `contour_labeler/compat.py`.
- plugins.qgis.org runs an automatic Qt6 check on upload (see the *Qt6 Check* tab).

## Credits

Concept, requirements and testing: Mats Elfström. Grew out of the PyQGIS script collection in
`pyqgis-cartography`.

## License

GPL-2.0-or-later - see [LICENSE](LICENSE).
