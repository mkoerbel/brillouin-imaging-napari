"""Pytest configuration for brillouin_imaging tests.

This module configures pytest for testing napari plugins.
It relies on fixtures provided by napari itself, including:
- make_napari_viewer: provided by napari.utils._testsupport
"""
import os
import sys
from types import SimpleNamespace

import pytest


# On macOS the offscreen Qt platform has no usable GL context, which
# causes vispy's glGetParameter to segfault.  Remove the offscreen
# override so the real display is used (tests need a GUI anyway).
if sys.platform == 'darwin':
    os.environ.pop('QT_QPA_PLATFORM', None)
else:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "qt: marks tests as requiring Qt (deselect with '-m \"not qt\"')"
    )


class _DummyVispyLayer:
    """Minimal stand-in for napari's vispy layer during headless tests."""

    def __init__(self):
        self.events = None
        self.node = SimpleNamespace(parent=None)
        self.order = 0
        self.first_visible = False

    def _on_camera_move(self, event=None):
        pass

    def _on_matrix_change(self):
        pass

    def _on_blending_change(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def _stub_vispy_layers_for_qt_tests(request, monkeypatch):
    """Avoid requiring an OpenGL-backed vispy layer in headless Qt tests."""
    if "qt" not in request.keywords:
        return

    def _add_layer(self, layer):
        self.canvas.layer_to_visual[layer] = _DummyVispyLayer()
        self.canvas._layer_overlay_to_visual[layer] = {}
        self.canvas._overlay_callbacks[layer] = lambda event=None: None

    def _remove_layer(self, event):
        layer = event.value
        self._overlay_callbacks.pop(layer, None)
        vispy_layer = self.layer_to_visual.pop(layer, None)
        if vispy_layer is not None:
            vispy_layer.close()
        self._layer_overlay_to_visual.pop(layer, None)

    monkeypatch.setattr("napari._qt.qt_viewer.QtViewer._add_layer", _add_layer)
    monkeypatch.setattr("napari._vispy.canvas.VispyCanvas._remove_layer", _remove_layer)


@pytest.fixture(autouse=True)
def _close_matplotlib_figures():
    """Close all matplotlib figures after every test.

    SpectraTools.__init__ creates several real figures via plt.subplots()
    (each wrapped in a Qt FigureCanvas), which registers them with
    pyplot's global figure manager. That manager keeps them alive
    regardless of whether the widget itself is garbage-collected, so
    without this, a full test run accumulates one leaked Figure (and its
    underlying Qt canvas) per SpectraTools construction — pytest already
    surfaces this as "More than 20 figures have been opened" partway
    through tests/test_spectra_tools.py. Left unchecked over a larger
    suite or a long-running session, this also keeps extra Qt widgets
    alive for the whole run, on top of whatever the matplotlib memory
    itself costs.
    """
    yield
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    plt.close("all")
