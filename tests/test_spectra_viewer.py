"""Tests for the spectra viewer module."""
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np

# Skip all tests in this module if imports fail due to missing dependencies
pytest.importorskip("matplotlib")
pytest.importorskip("matplotlib.backends.backend_qt5agg")

try:
    from brillouin_imaging._spectra_viewer import ShowSpectrum
    SPECTRA_VIEWER_AVAILABLE = True
except ImportError:
    SPECTRA_VIEWER_AVAILABLE = False
    ShowSpectrum = None


@pytest.mark.skipif(not SPECTRA_VIEWER_AVAILABLE, reason="Spectra viewer module not available")
class TestShowSpectrum:
    """Tests for ShowSpectrum widget."""

    @pytest.mark.qt
    def test_show_spectrum_initialization(self, qtbot, make_napari_viewer):
        """Test that ShowSpectrum widget initializes correctly."""
        # Create a viewer using the napari fixture
        viewer = make_napari_viewer()
        
        # Initialize the widget
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify basic attributes are set
        assert widget._viewer == viewer
        assert hasattr(widget, 'fig')
        assert hasattr(widget, 'ax')
        assert widget.spectrum_ymax == 0
        assert widget.spectrum_ymin == 1E6

    @pytest.mark.qt
    def test_show_spectrum_has_checkbox(self, qtbot, make_napari_viewer):
        """Test that ShowSpectrum widget has autoscale checkbox."""
        viewer = make_napari_viewer()
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify the checkbox exists
        assert hasattr(widget, '_invert_checkbox')
        assert widget._invert_checkbox.text == "Autoscale y-axis"

    @pytest.mark.qt
    def test_reset_autoscale(self, qtbot, make_napari_viewer):
        """Test the _reset_autoscale method."""
        viewer = make_napari_viewer()
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Modify the values
        widget.spectrum_ymax = 100
        widget.spectrum_ymin = 10
        
        # Reset autoscale
        widget._reset_autoscale()
        
        # Verify values are reset
        assert widget.spectrum_ymax == 0
        assert widget.spectrum_ymin == 1E6

    @pytest.mark.qt
    def test_load_spectrum_checks_layer_visibility(self, qtbot, make_napari_viewer):
        """Test that _load_spectrum returns early if layer is not visible."""
        viewer = make_napari_viewer()
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Create a mock layer with invisible state
        mock_layer = MagicMock()
        mock_layer.visible = False
        mock_layer.metadata = {
            'brimfile': MagicMock(),
            'Data_group': 0
        }
        mock_layer.data.shape = (10, 10, 10)
        
        # Call _load_spectrum
        widget._load_spectrum((1, 1, 1), mock_layer)
        
        # Verify that get_spectrum_in_image was not called
        mock_layer.metadata['brimfile'].get_data.assert_not_called()

    @pytest.mark.qt
    def test_load_spectrum_checks_coordinates_within_bounds(self, qtbot, make_napari_viewer):
        """Test that _load_spectrum returns early for out-of-bounds coordinates."""
        viewer = make_napari_viewer()
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Create a mock layer
        mock_layer = MagicMock()
        mock_layer.visible = True
        mock_layer.metadata = {
            'brimfile': MagicMock(),
            'Data_group': 0
        }
        mock_layer.data.shape = (5, 5, 5)
        
        # Call with out-of-bounds coordinate
        widget._load_spectrum((10, 10, 10), mock_layer)
        
        # Verify that get_spectrum_in_image was not called
        mock_layer.metadata['brimfile'].get_data.assert_not_called()

    @pytest.mark.qt
    def test_load_spectrum_plots_spectrum(self, qtbot, make_napari_viewer):
        """Test that _load_spectrum plots the spectrum correctly."""
        viewer = make_napari_viewer()
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Create mock spectrum data
        frequencies = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        psd = np.array([10.0, 20.0, 15.0, 25.0, 30.0])
        
        # Create a mock file and layer
        mock_file = MagicMock()
        mock_data_group = MagicMock()
        mock_data_group.get_spectrum_in_image.return_value = (psd, frequencies, None, 'GHz')
        mock_file.get_data.return_value = mock_data_group
        
        mock_layer = MagicMock()
        mock_layer.visible = True
        mock_layer.name = "Test Layer"
        mock_layer.metadata = {
            'brimfile': mock_file,
            'Data_group': 0
        }
        mock_layer.data.shape = (10, 10, 10)
        
        # Call _load_spectrum with valid coordinates
        coord = (1, 2, 3)
        widget._load_spectrum(coord, mock_layer)
        
        # Verify that the spectrum was requested
        mock_data_group.get_spectrum_in_image.assert_called_once_with(coord)
        
        # Verify that the plot was updated
        assert widget.spectrum_ymax >= max(psd)
        assert widget.spectrum_ymin <= min(psd)


@pytest.mark.skipif(not SPECTRA_VIEWER_AVAILABLE, reason="Spectra viewer module not available")
class TestShowSpectrumIntegration:
    """Integration tests for ShowSpectrum widget."""

    @pytest.mark.qt
    def test_widget_creation_does_not_raise(self, qtbot, make_napari_viewer):
        """Test that creating the widget doesn't raise any errors."""
        viewer = make_napari_viewer()
        
        # This should not raise
        widget = ShowSpectrum(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Basic sanity checks
        assert widget is not None
        assert len(widget) > 0  # Should have at least one widget (checkbox)
