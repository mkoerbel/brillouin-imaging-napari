"""Tests for the spectra viewer module."""
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np

try:
    import brillouin_imaging._spectra_tools as spectra_tools_module
    from brillouin_imaging._spectra_tools import SpectraTools
    MATPLOTLIB_AVAILABLE = spectra_tools_module._MATPLOTLIB_IMPORT_ERROR is None
    SPECTRA_TOOLS_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    SPECTRA_TOOLS_AVAILABLE = False
    SpectraTools = None
    spectra_tools_module = None


def test_spectra_tools_warns_when_matplotlib_missing(monkeypatch):
    """Test that the widget raises ImportError before Container init."""
    monkeypatch.setattr(
        spectra_tools_module,
        "_MATPLOTLIB_IMPORT_ERROR",
        ImportError("matplotlib missing"),
    )

    with patch.object(
        spectra_tools_module.Container, "__init__", autospec=True
    ) as container_init:
        with pytest.raises(ImportError):
            SpectraTools(MagicMock())

    container_init.assert_not_called()


@pytest.mark.skipif(
    not MATPLOTLIB_AVAILABLE,
    reason="Spectra tools GUI tests require matplotlib",
)
@pytest.mark.skipif(not SPECTRA_TOOLS_AVAILABLE, reason="Spectra tools module not available")
class TestSpectraTools:
    """Tests for SpectraTools widget."""

    @pytest.mark.qt
    def test_spectra_tools_initialization(self, qtbot, make_napari_viewer):
        """Test that SpectraTools widget initializes correctly."""
        # Create a viewer using the napari fixture
        viewer = make_napari_viewer()
        
        # Initialize the widget
        widget = SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify basic attributes are set
        assert widget._viewer == viewer
        assert hasattr(widget, 'fig')
        assert hasattr(widget, 'ax')
        assert widget.spectrum_ymax == 0
        assert widget.spectrum_ymin == 1E6

    @pytest.mark.qt
    def test_spectra_tools_has_checkbox(self, qtbot, make_napari_viewer):
        """Test that SpectraTools widget has autoscale checkbox."""
        viewer = make_napari_viewer()
        widget = SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify the checkbox exists
        assert hasattr(widget, '_autoscale_checkbox')
        assert widget._autoscale_checkbox.text() == "Autoscale y-axis"

    @pytest.mark.qt
    def test_tabs_and_spectral_image_controls(self, qtbot, make_napari_viewer):
        """Verify QTabWidget exists and spectral image controls are present."""
        viewer = make_napari_viewer()
        widget = SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        # find QTabWidget in native children
        from qtpy.QtWidgets import QTabWidget
        tabs = widget.native.findChildren(QTabWidget)
        assert len(tabs) >= 1

        # verify tab labels exist
        tab_widget = tabs[0]
        assert tab_widget.count() >= 3
        tab_names = [tab_widget.tabText(i) for i in range(tab_widget.count())]
        assert "Plot Spectrum at Pixel" in tab_names
        assert "Create Spectral Image" in tab_names
        assert "Regional Spectra Analysis" in tab_names

        # spectral image controls
        assert hasattr(widget, '_num_field1')
        assert hasattr(widget, '_num_field2')
        assert hasattr(widget, '_create_btn')
        assert widget._num_field1.maximumWidth() > 0

    @pytest.mark.qt
    def test_update_labels_combobox_and_create_labels(self, qtbot, make_napari_viewer):
        """Test labels combobox updates with matching labels layers and create_labels_layer."""
        viewer = make_napari_viewer()
        widget = SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        # add a brimfile-like image layer and set as active selection
        data = np.zeros((10, 10, 3))
        img = viewer.add_image(data, name='brim_img')
        img.metadata = {'is_brimfile': True, 'brimfile': MagicMock(), 'Data_group': 0}
        viewer.layers.selection.active = img

        # add a labels layer with matching shape/scale
        labels = viewer.add_labels(np.zeros_like(data, dtype=np.uint8), name='test_labels')

        # add a labels layer with mismatching shape (should not be included)
        viewer.add_labels(np.zeros((9, 10, 3), dtype=np.uint8), name='wrong_shape_labels')

        # napari auto-switches active layer to the last added layer,
        # so we must re-select the brimfile image before updating.
        viewer.layers.selection.active = img

        # call update and check combobox contains the labels layer name
        widget._update_labels_combobox()
        assert widget._labels_combobox.count() >= 1
        names = [widget._labels_combobox.itemText(i) for i in range(widget._labels_combobox.count())]
        assert 'test_labels' in names
        assert 'wrong_shape_labels' not in names

        # now test creating a new labels layer via the method
        # select the brim image as active and call create
        viewer.layers.selection.active = img
        widget._create_labels_layer()
        # a new labels layer should be present with expected name prefix
        labels_names = [lyr.name for lyr in viewer.layers if isinstance(lyr, type(labels))]
        assert any(name.startswith('Labels for') for name in labels_names)

    @pytest.mark.qt
    def test_create_labels_layer_requires_brimfile_layer(self, qtbot, make_napari_viewer):
        """_create_labels_layer should show info and not create when active is not brimfile."""
        viewer = make_napari_viewer()
        widget = SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        img = viewer.add_image(np.zeros((5, 5, 2)), name='non_brim')
        img.metadata = {}
        viewer.layers.selection.active = img

        with patch('napari.utils.notifications.show_info') as show_info:
            before = len([lyr for lyr in viewer.layers if lyr.__class__.__name__ == 'Labels'])
            widget._create_labels_layer()
            after = len([lyr for lyr in viewer.layers if lyr.__class__.__name__ == 'Labels'])
            assert after == before
            show_info.assert_called()

    @pytest.mark.qt
    def test_create_spectral_image_adds_image_layer(self, qtbot, make_napari_viewer):
        """_on_create_spectral_image should add an image layer for a valid brimfile layer."""
        viewer = make_napari_viewer()
        widget = SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        # Create an active brimfile-like layer
        data = np.zeros((6, 7, 2))
        img_layer = viewer.add_image(data, name='brim_img')

        mock_file = MagicMock()
        mock_data_group = MagicMock()
        mock_ar = MagicMock()

        # PSD map: intensities and frequencies with last axis = 5 samples
        intensities = np.ones((6, 7, 2, 5), dtype=float)
        freqs = np.linspace(-30, 30, 5, dtype=float)
        freqs = np.broadcast_to(freqs, (6, 7, 2, 5))
        mock_data_group.get_PSD_as_spatial_map.return_value = (intensities, freqs)

        offset_img = np.zeros((6, 7, 2), dtype=float)
        mock_ar.get_image.return_value = (offset_img, None)
        mock_data_group.get_analysis_results.return_value = mock_ar
        mock_file.get_data.return_value = mock_data_group

        img_layer.metadata = {
            'is_brimfile': True,
            'brimfile': mock_file,
            'Data_group': 0,
            'Analysis_result': 0,
        }
        viewer.layers.selection.active = img_layer

        # set bounds to include all freqs
        widget._num_field1.setValue(-30)
        widget._num_field2.setValue(30)

        before_count = len(viewer.layers)
        widget._on_create_spectral_image()
        after_count = len(viewer.layers)

        assert after_count == before_count + 1
        new_layer = viewer.layers[-1]
        assert new_layer.name.startswith('Spectral image from')

    @pytest.mark.qt
    def test_reset_autoscale(self, qtbot, make_napari_viewer):
        """Test the _reset_autoscale method."""
        viewer = make_napari_viewer()
        widget = SpectraTools(viewer)
        
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
        widget = SpectraTools(viewer)
        
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
        widget = SpectraTools(viewer)
        
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
        widget = SpectraTools(viewer)
        
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


@pytest.mark.skipif(
    not MATPLOTLIB_AVAILABLE,
    reason="Spectra tools integration tests require matplotlib",
)
@pytest.mark.skipif(not SPECTRA_TOOLS_AVAILABLE, reason="Spectra tools module not available")
class TestSpectraToolsIntegration:
    """Integration tests for SpectraTools widget."""

    @pytest.mark.qt
    def test_widget_creation_does_not_raise(self, qtbot, make_napari_viewer):
        """Test that creating the widget doesn't raise any errors."""
        viewer = make_napari_viewer()
        
        # This should not raise
        widget = SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Basic sanity checks
        assert widget is not None
        # The widget uses raw Qt layouts rather than magicgui children,
        # so check that the native Qt widget has children.
        assert widget.native.layout().count() > 0
