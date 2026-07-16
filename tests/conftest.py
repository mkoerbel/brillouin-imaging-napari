"""Pytest configuration for brillouin_imaging tests.

This module configures pytest for testing napari plugins.
It relies on fixtures provided by napari itself, including:
- make_napari_viewer: provided by napari.utils._testsupport

CI provides a real, working display and OpenGL context on every OS via
the `pyvista/setup-headless-display-action` step in
.github/workflows/test.yml (Xvfb + a window manager on Linux, Mesa3D on
Windows, the runner's native display on macOS), so no QT_QPA_PLATFORM
override or vispy/GL monkeypatching is needed here.
"""
import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "qt: marks tests as requiring Qt (deselect with '-m \"not qt\"')"
    )


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
