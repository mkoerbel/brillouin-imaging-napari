"""Pytest configuration for brillouin_imaging tests.

This module configures pytest for testing napari plugins.
It relies on fixtures provided by napari itself, including:
- make_napari_viewer: provided by napari.utils._testsupport
"""
import os


# Set QT_QPA_PLATFORM to offscreen for headless testing
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "qt: marks tests as requiring Qt (deselect with '-m \"not qt\"')"
    )

