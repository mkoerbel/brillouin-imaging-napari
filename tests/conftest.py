"""Pytest configuration for brillouin_imaging tests.

This module configures pytest for testing napari plugins.
It relies on fixtures provided by napari itself, including:
- make_napari_viewer: provided by napari.utils._testsupport
"""
import os
import sys


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

