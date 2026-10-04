# Translations

Source strings are English. Swedish lives in `contour_labeler_sv.ts` and is shown
automatically when QGIS runs with a Swedish locale (`plugin.py` loads
`i18n/contour_labeler_<locale>.qm`).

The `.ts` files are maintained by hand (the panel uses a small `_tr()` wrapper that
`lupdate` does not recognise). After editing a `.ts`, compile it and commit the `.qm`
too, so that CI-built packages contain the translation:

```bash
pyside6-lrelease contour_labeler/i18n/contour_labeler_sv.ts -qm contour_labeler/i18n/contour_labeler_sv.qm
```

To add a language, copy `contour_labeler_sv.ts`, change `language="sv"` and translate.
