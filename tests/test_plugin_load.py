"""Load the plugin inside a real QGIS (skipped when QGIS is not importable)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.core")

from qgis.testing import start_app  # noqa: E402
from qgis.testing.mocked import get_iface  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

start_app()


def test_class_factory_and_lifecycle():
    from contour_labeler import classFactory

    plugin = classFactory(get_iface())
    plugin.initGui()
    plugin.unload()


def test_first_click_shows_dock_then_toggles():
    from qgis.gui import QgsMapCanvas
    from qgis.PyQt.QtWidgets import QMainWindow

    from contour_labeler.plugin import ContourLabelerPlugin

    window = QMainWindow()
    canvas = QgsMapCanvas()

    class Iface:
        def mainWindow(self):
            return window

        def mapCanvas(self):
            return canvas

        def addDockWidget(self, area, dock):
            window.addDockWidget(area, dock)

    plugin = ContourLabelerPlugin(Iface())
    window.show()
    plugin.run()  # first click
    assert plugin.dock.isVisible()
    plugin.run()  # second click hides
    assert not plugin.dock.isVisible()
    plugin.run()
    assert plugin.dock.isVisible()
    plugin.dock.cleanup()


def test_help_entry_in_menu_opens_localised_url(monkeypatch):
    from qgis.PyQt.QtGui import QDesktopServices
    from qgis.PyQt.QtWidgets import QMainWindow

    from contour_labeler import plugin as plugin_module

    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()))

    class Iface:
        def __init__(self):
            self.menu = []
            self.window = QMainWindow()

        def mainWindow(self):
            return self.window

        def addToolBarIcon(self, action):
            pass

        def removeToolBarIcon(self, action):
            pass

        def addPluginToMenu(self, menu, action):
            self.menu.append(action)

        def removePluginMenu(self, menu, action):
            self.menu.remove(action)

    iface = Iface()
    plugin = plugin_module.ContourLabelerPlugin(iface)
    plugin.initGui()
    assert len(iface.menu) == 2  # the tool and its Help entry

    plugin.locale = "en"
    plugin.help_action.trigger()
    plugin.locale = "sv"
    plugin.help_action.trigger()
    assert opened == [plugin_module.HELP_URL, plugin_module.HELP_URLS["sv"]]

    plugin.unload()
    assert iface.menu == []
