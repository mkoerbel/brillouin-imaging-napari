"""Tests for the spectra viewer module."""
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

try:
    import brillouin_imaging._spectra_tools as spectra_tools_module
    MATPLOTLIB_AVAILABLE = spectra_tools_module._MATPLOTLIB_IMPORT_ERROR is None
    SPECTRA_TOOLS_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    SPECTRA_TOOLS_AVAILABLE = False
    spectra_tools_module = None


@pytest.mark.skipif(not SPECTRA_TOOLS_AVAILABLE, reason="Spectra tools module not available")
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
            spectra_tools_module.SpectraTools(MagicMock())

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
        widget = spectra_tools_module.SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify basic attributes are set
        assert widget._viewer == viewer
        assert hasattr(widget, 'fig_plot_spectrum')
        assert hasattr(widget, 'ax_plot_spectrum')
        assert widget.spectrum_ymax == 0
        assert widget.spectrum_ymin == 1E6

    @pytest.mark.qt
    def test_spectra_tools_has_checkbox(self, qtbot, make_napari_viewer):
        """Test that SpectraTools widget has autoscale checkbox."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify the checkbox exists
        assert hasattr(widget, '_autoscale_checkbox')
        assert widget._autoscale_checkbox.text() == "Autoscale y-axis"

    @pytest.mark.qt
    def test_tabs_and_spectral_image_controls(self, qtbot, make_napari_viewer):
        """Verify QTabWidget exists and spectral image controls are present."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
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
        widget = spectra_tools_module.SpectraTools(viewer)
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
        widget = spectra_tools_module.SpectraTools(viewer)
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
        widget = spectra_tools_module.SpectraTools(viewer)
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
    def test_create_spectral_image_noop_no_active_layer(self, qtbot, make_napari_viewer):
        """_on_create_spectral_image should do nothing without an active layer."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        before_count = len(viewer.layers)
        widget._on_create_spectral_image()
        assert len(viewer.layers) == before_count

    @pytest.mark.qt
    def test_create_spectral_image_noop_invisible_layer(self, qtbot, make_napari_viewer):
        """_on_create_spectral_image should do nothing for an invisible layer."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        layer = viewer.add_image(np.zeros((3, 3)), name='brim_img')
        layer.metadata = {'is_brimfile': True, 'brimfile': MagicMock()}
        layer.visible = False
        viewer.layers.selection.active = layer

        before_count = len(viewer.layers)
        widget._on_create_spectral_image()
        assert len(viewer.layers) == before_count

    @pytest.mark.qt
    def test_create_spectral_image_noop_non_brimfile_layer(self, qtbot, make_napari_viewer):
        """_on_create_spectral_image should show info for a non-brimfile layer."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        layer = viewer.add_image(np.zeros((3, 3)), name='non_brim')
        layer.metadata = {}
        viewer.layers.selection.active = layer

        before_count = len(viewer.layers)
        with patch('napari.utils.notifications.show_info') as show_info:
            widget._on_create_spectral_image()
        show_info.assert_called_once()
        assert len(viewer.layers) == before_count

    @pytest.mark.qt
    def test_create_spectral_image_swaps_reversed_bounds(self, qtbot, make_napari_viewer):
        """Lower/upper bound fields should be swapped if entered in reverse order."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        data = np.zeros((2, 2, 2))
        img_layer = viewer.add_image(data, name='brim_img')

        mock_file = MagicMock()
        mock_data_group = MagicMock()
        mock_ar = MagicMock()
        intensities = np.ones((2, 2, 2, 5), dtype=float)
        freqs = np.broadcast_to(
            np.linspace(-30, 30, 5, dtype=float), (2, 2, 2, 5)
        )
        mock_data_group.get_PSD_as_spatial_map.return_value = (intensities, freqs)
        offset_img = np.zeros((2, 2, 2), dtype=float)
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

        # Enter bounds in reverse order (lower > upper).
        widget._num_field1.setValue(30)
        widget._num_field2.setValue(-30)

        widget._on_create_spectral_image()

        assert widget._num_field1.value() == -30
        assert widget._num_field2.value() == 30

    @pytest.mark.qt
    def test_create_spectral_image_warns_on_partial_coverage(self, qtbot, make_napari_viewer):
        """A frequency range that misses some pixels should show an info message."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        data = np.zeros((1, 2, 1))
        img_layer = viewer.add_image(data, name='brim_img')

        mock_file = MagicMock()
        mock_data_group = MagicMock()
        mock_ar = MagicMock()
        intensities = np.ones((1, 2, 1, 5), dtype=float)
        # Second pixel's frequencies never fall inside the selected range.
        freqs = np.zeros((1, 2, 1, 5), dtype=float)
        freqs[0, 0, 0, :] = np.linspace(-30, 30, 5)
        freqs[0, 1, 0, :] = np.linspace(100, 140, 5)
        mock_data_group.get_PSD_as_spatial_map.return_value = (intensities, freqs)
        offset_img = np.zeros((1, 2, 1), dtype=float)
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

        widget._num_field1.setValue(-30)
        widget._num_field2.setValue(30)

        with patch('napari.utils.notifications.show_info') as show_info:
            widget._on_create_spectral_image()

        show_info.assert_called_once()

    @pytest.mark.qt
    def test_create_labels_layer_noop_no_active_layer(self, qtbot, make_napari_viewer):
        """_create_labels_layer should do nothing without an active layer."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        before_count = len(viewer.layers)
        widget._create_labels_layer()
        assert len(viewer.layers) == before_count

    @pytest.mark.qt
    def test_reset_autoscale(self, qtbot, make_napari_viewer):
        """Test the _reset_autoscale method."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        
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
        widget = spectra_tools_module.SpectraTools(viewer)
        
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
        widget = spectra_tools_module.SpectraTools(viewer)
        
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
        widget = spectra_tools_module.SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Create mock spectrum data
        frequencies = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        psd = np.array([10.0, 20.0, 15.0, 25.0, 30.0])
        
        # Create a mock file and layer
        mock_file = MagicMock()
        mock_data_group = MagicMock()
        mock_data_group.get_spectrum_in_image.return_value = (psd, frequencies, None, 'GHz')

        mock_analysis_result = MagicMock()
        mock_analysis_result.fit_model = "Lorentzian"
        mock_analysis_result.get_all_quantities_in_image.return_value = {
            'Shift': {},
            'Width': {},
            'Amplitude': {},
            'Offset': {},
        }
        mock_data_group.get_analysis_results.return_value = mock_analysis_result
        mock_file.get_data.return_value = mock_data_group
        
        mock_layer = MagicMock()
        mock_layer.visible = True
        mock_layer.name = "Test Layer"
        mock_layer.metadata = {
            'brimfile': mock_file,
            'Data_group': 0,
            'Analysis_result': 0,
        }
        mock_layer.data.shape = (10, 10, 10)
        
        # Call _load_spectrum with valid coordinates
        coord = (1, 2, 3)
        with patch.object(
            spectra_tools_module.brim.fitting_models,
            'get_fit_model',
            return_value=lambda x, nu0, gamma, a, b: np.zeros_like(x),
        ):
            widget._load_spectrum(coord, mock_layer)
        
        # Verify that the spectrum was requested
        mock_data_group.get_spectrum_in_image.assert_called_once_with(coord)
        
        # Verify that the plot was updated
        assert widget.spectrum_ymax >= max(psd)
        assert widget.spectrum_ymin <= min(psd)

    @pytest.mark.qt
    def test_load_spectrum_splits_on_frequency_jump_and_plots_both_fits(
        self, qtbot, make_napari_viewer
    ):
        """Frequency gaps should split the plotted line, and both Stokes and
        AntiStokes fits should be drawn when both are present."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        # Two clusters of frequencies with a large gap between them.
        frequencies = np.array([1.0, 2.0, 3.0, 50.0, 51.0, 52.0])
        psd = np.array([10.0, 20.0, 15.0, 25.0, 30.0, 12.0])

        mock_file = MagicMock()
        mock_data_group = MagicMock()
        mock_data_group.get_spectrum_in_image.return_value = (
            psd, frequencies, None, 'GHz'
        )

        quantity = MagicMock()
        quantity.value = 1.0
        mock_analysis_result = MagicMock()
        mock_analysis_result.fit_model = "Lorentzian"
        mock_analysis_result.get_all_quantities_in_image.return_value = {
            'Shift': {'Stokes': quantity, 'AntiStokes': quantity},
            'Width': {'Stokes': quantity, 'AntiStokes': quantity},
            'Amplitude': {'Stokes': quantity, 'AntiStokes': quantity},
            'Offset': {'Stokes': quantity, 'AntiStokes': quantity},
        }
        mock_data_group.get_analysis_results.return_value = mock_analysis_result
        mock_file.get_data.return_value = mock_data_group

        mock_layer = MagicMock()
        mock_layer.visible = True
        mock_layer.name = "Test Layer"
        mock_layer.metadata = {
            'brimfile': mock_file,
            'Data_group': 0,
            'Analysis_result': 0,
        }
        mock_layer.data.shape = (10, 10, 10)

        coord = (1, 2, 3)
        with patch.object(
            spectra_tools_module.brim.fitting_models,
            'get_fit_model',
            return_value=lambda x, nu0, gamma, a, b: np.zeros_like(x),
        ):
            widget._load_spectrum(coord, mock_layer)

        # Two segments for the split raw spectrum + two fit lines
        # (Stokes and AntiStokes) = 4 lines total.
        assert len(widget.ax_plot_spectrum.lines) == 4

    @pytest.mark.qt
    def test_load_vipa_rawdata_plots_image_and_overlay(self, qtbot, make_napari_viewer):
        """Test that _load_VIPA_rawdata draws the raw image and spectral line overlay."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)

        qtbot.addWidget(widget.native)

        raw_image = np.arange(16, dtype=float).reshape(4, 4)
        spectral_line = (1, 0, 2, 3)
        linewidth = 2
        coord = (1, 1, 1)

        mock_file = MagicMock()
        mock_file.subtype = spectra_tools_module.brim.subtypes.SubType.SinglePoint_VIPA_v0_1

        mock_layer = MagicMock()
        mock_layer.visible = True
        mock_layer.data.shape = (4, 4, 4)
        mock_layer.metadata = {
            'brimfile': mock_file,
            'Data_group': 0,
        }

        with patch.object(
            spectra_tools_module.single_point_VIPA,
            'get_raw_spectrum_in_image',
            return_value=(raw_image, spectral_line, linewidth),
        ):
            widget._load_VIPA_rawdata(coord, mock_layer)

        assert len(widget.ax_vipa_rawdata.images) == 1
        assert len(widget.ax_vipa_rawdata.lines) == 1
        assert np.array_equal(widget.ax_vipa_rawdata.images[0].get_array(), raw_image)

        line = widget.ax_vipa_rawdata.lines[0]
        assert np.array_equal(line.get_xdata(), np.array([0, 3]))
        assert np.array_equal(line.get_ydata(), np.array([1, 2]))

    @pytest.mark.qt
    def test_load_vipa_rawdata_ignored_for_wrong_subtype(self, qtbot, make_napari_viewer):
        """_load_VIPA_rawdata should be a no-op for non-VIPA files."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        mock_file = MagicMock()
        mock_file.subtype = "some_other_subtype"
        mock_layer = MagicMock()
        mock_layer.visible = True
        mock_layer.data.shape = (4, 4, 4)
        mock_layer.metadata = {'brimfile': mock_file, 'Data_group': 0}

        widget._load_VIPA_rawdata((1, 1, 1), mock_layer)

        assert len(widget.ax_vipa_rawdata.images) == 0

    @pytest.mark.qt
    def test_mouse_event_is_valid_bounds(self, qtbot, make_napari_viewer):
        """Test _mouse_event_is_valid for visibility and coordinate bounds."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        mock_layer = MagicMock()
        mock_layer.visible = False
        mock_layer.data.shape = (5, 5, 5)
        assert widget._mouse_event_is_valid((1, 1, 1), mock_layer) is False

        mock_layer.visible = True
        assert widget._mouse_event_is_valid((1, 1, 1), mock_layer) is True
        assert widget._mouse_event_is_valid((-1, 1, 1), mock_layer) is False
        assert widget._mouse_event_is_valid((5, 1, 1), mock_layer) is False

    @pytest.mark.qt
    def test_linewidth_data_to_points_edge_cases(self, qtbot, make_napari_viewer):
        """Test _linewidth_data_to_points None/non-positive/degenerate segment."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        # None linewidth defaults to 1.0 and still returns a positive value.
        result = widget._linewidth_data_to_points(None, 0, 0, 1, 1)
        assert result > 0

        # Non-positive linewidth returns the minimum value.
        assert widget._linewidth_data_to_points(0, 0, 0, 1, 1) == 0.1
        assert widget._linewidth_data_to_points(-5, 0, 0, 1, 1) == 0.1

        # Degenerate segment (start == end) still returns a positive value.
        result = widget._linewidth_data_to_points(2, 3, 3, 3, 3)
        assert result > 0

    @pytest.mark.qt
    def test_on_click_ignores_no_active_layer(self, qtbot, make_napari_viewer):
        """The mouse callback should do nothing if there is no active layer."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        callback = widget._viewer.mouse_drag_callbacks[-1]
        event = MagicMock(type='mouse_press', position=(0, 0, 0))

        with patch.object(spectra_tools_module.SpectraTools, '_load_spectrum') as mock_load_spectrum, \
             patch.object(spectra_tools_module.SpectraTools, '_load_VIPA_rawdata') as mock_vipa:
            gen = callback(viewer, event)
            with pytest.raises(StopIteration):
                next(gen)

        mock_load_spectrum.assert_not_called()
        mock_vipa.assert_not_called()

    @pytest.mark.qt
    def test_on_click_ignores_non_brimfile_layer(self, qtbot, make_napari_viewer):
        """The mouse callback should ignore layers without brimfile metadata."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        layer = viewer.add_image(np.zeros((3, 3, 3)), name='non_brim')
        layer.metadata = {}
        viewer.layers.selection.active = layer

        callback = widget._viewer.mouse_drag_callbacks[-1]
        event = MagicMock(type='mouse_press', position=(0, 0, 0))

        with patch.object(spectra_tools_module.SpectraTools, '_load_spectrum') as mock_load_spectrum, \
             patch.object(spectra_tools_module.SpectraTools, '_load_VIPA_rawdata') as mock_vipa:
            gen = callback(viewer, event)
            with pytest.raises(StopIteration):
                next(gen)

        mock_load_spectrum.assert_not_called()
        mock_vipa.assert_not_called()

    @pytest.mark.qt
    def test_on_click_calls_load_spectrum_on_simple_click(self, qtbot, make_napari_viewer):
        """A click without any mouse-move events should load the spectrum."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        layer = viewer.add_image(np.zeros((3, 3, 3)), name='brim_img')
        layer.metadata = {
            'is_brimfile': True,
            'brimfile': MagicMock(),
            'Data_group': 0,
        }
        viewer.layers.selection.active = layer

        callback = widget._viewer.mouse_drag_callbacks[-1]
        event = MagicMock(type='mouse_press', position=(1, 1, 1))

        with patch.object(spectra_tools_module.SpectraTools, '_load_spectrum') as mock_load_spectrum, \
             patch.object(spectra_tools_module.SpectraTools, '_load_VIPA_rawdata') as mock_vipa:
            gen = callback(viewer, event)
            next(gen)  # advance to the first yield (waiting for release/move)
            event.type = 'mouse_release'
            with pytest.raises(StopIteration):
                next(gen)

        mock_load_spectrum.assert_called_once()
        mock_vipa.assert_called_once()

    @pytest.mark.qt
    def test_on_click_ignores_drag(self, qtbot, make_napari_viewer):
        """A drag (mouse-move events) should not trigger spectrum loading."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        layer = viewer.add_image(np.zeros((3, 3, 3)), name='brim_img')
        layer.metadata = {
            'is_brimfile': True,
            'brimfile': MagicMock(),
            'Data_group': 0,
        }
        viewer.layers.selection.active = layer

        callback = widget._viewer.mouse_drag_callbacks[-1]
        event = MagicMock(type='mouse_press', position=(1, 1, 1))

        with patch.object(spectra_tools_module.SpectraTools, '_load_spectrum') as mock_load_spectrum, \
             patch.object(spectra_tools_module.SpectraTools, '_load_VIPA_rawdata') as mock_vipa:
            gen = callback(viewer, event)
            next(gen)  # first yield
            event.type = 'mouse_move'
            next(gen)  # dragged = True, loop continues
            event.type = 'mouse_release'
            with pytest.raises(StopIteration):
                next(gen)

        mock_load_spectrum.assert_not_called()
        mock_vipa.assert_not_called()

    @pytest.mark.qt
    def test_update_metadata_table_no_active_layer(self, qtbot, make_napari_viewer):
        """_update_metadata_table should clear rows and return if no active layer."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        widget._update_metadata_table()
        assert widget._metadata_table.rowCount() == 0

    @pytest.mark.qt
    def test_update_metadata_table_ignores_non_brimfile_layer(self, qtbot, make_napari_viewer):
        """_update_metadata_table should ignore layers without brimfile metadata."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        layer = viewer.add_image(np.zeros((3, 3)), name='non_brim')
        layer.metadata = {}
        viewer.layers.selection.active = layer

        widget._update_metadata_table()
        assert widget._metadata_table.rowCount() == 0

    @pytest.mark.qt
    def test_update_metadata_table_populates_rows(self, qtbot, make_napari_viewer):
        """_update_metadata_table should populate header + value rows, skipping IRF."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        item_with_units = MagicMock()
        item_with_units.units = 'GHz'
        item_with_units.value = 1.23

        item_without_units = MagicMock(spec=[])
        # spec=[] means hasattr(item, 'units')/'value' is False -> str(item) branch

        metadata_dict = {
            'General': {
                'Sample': item_with_units,
                'IRF': MagicMock(),  # should be skipped
                'IRF_frequency': MagicMock(),  # should be skipped
                'Note': item_without_units,
            },
            'invalid_section': 'not a dict',
        }

        mock_metadata = MagicMock()
        mock_metadata.all_to_dict.return_value = metadata_dict
        mock_data_group = MagicMock()
        mock_data_group.get_metadata.return_value = mock_metadata
        mock_file = MagicMock()
        mock_file.get_data.return_value = mock_data_group

        layer = viewer.add_image(np.zeros((3, 3)), name='brim_img')
        layer.metadata = {
            'is_brimfile': True,
            'brimfile': mock_file,
            'Data_group': 0,
        }
        viewer.layers.selection.active = layer

        with patch('napari.utils.notifications.show_info') as show_info:
            widget._update_metadata_table()

        # 1 header row + 2 value rows (Sample, Note); IRF rows skipped.
        assert widget._metadata_table.rowCount() == 3
        header_text = widget._metadata_table.item(0, 0).text()
        assert header_text == 'General'
        row_labels = [
            widget._metadata_table.item(r, 0).text()
            for r in range(1, widget._metadata_table.rowCount())
        ]
        assert any('Sample' in label for label in row_labels)
        assert any('Note' in label for label in row_labels)
        # The invalid (non-dict) section should trigger a notification.
        show_info.assert_called_once()


@pytest.mark.skipif(
    not MATPLOTLIB_AVAILABLE,
    reason="Spectra tools GUI tests require matplotlib",
)
@pytest.mark.skipif(not SPECTRA_TOOLS_AVAILABLE, reason="Spectra tools module not available")
class TestPlotLabelsSpectrum:
    """Tests for _plot_labels_spectrum."""

    @pytest.mark.qt
    def test_no_labels_selected_shows_info(self, qtbot, make_napari_viewer):
        """Nothing selected in the labels combobox should show an info message."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        with patch('napari.utils.notifications.show_info') as show_info:
            widget._plot_labels_spectrum()

        show_info.assert_called_once()

    @pytest.mark.qt
    def test_no_labels_in_layer_shows_info(self, qtbot, make_napari_viewer):
        """An all-zero labels layer should show an info message."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        viewer.add_labels(np.zeros((1, 2, 2), dtype=np.uint8), name='empty_labels')
        widget._labels_combobox.addItem('empty_labels')
        widget._labels_combobox.setCurrentText('empty_labels')

        with patch('napari.utils.notifications.show_info') as show_info:
            widget._plot_labels_spectrum()

        show_info.assert_called_once()

    @pytest.mark.qt
    def test_no_brimfile_layer_selected_shows_info(self, qtbot, make_napari_viewer):
        """No active brimfile layer should show an info message."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        viewer.add_labels(np.ones((1, 2, 2), dtype=np.uint8), name='labels')
        widget._labels_combobox.addItem('labels')
        widget._labels_combobox.setCurrentText('labels')

        non_brim_layer = viewer.add_image(np.zeros((1, 2, 2)), name='non_brim')
        non_brim_layer.metadata = {}
        viewer.layers.selection.active = non_brim_layer

        with patch('napari.utils.notifications.show_info') as show_info:
            widget._plot_labels_spectrum()

        show_info.assert_called_once()

    @pytest.mark.qt
    def test_plots_averaged_spectra_and_fills_table(self, qtbot, make_napari_viewer):
        """Full happy-path: average spectra per label and populate the summary table."""
        viewer = make_napari_viewer()
        widget = spectra_tools_module.SpectraTools(viewer)
        qtbot.addWidget(widget.native)

        # Shape: z=1, y=2, x=2, nfreq=5
        freqs = np.linspace(-2, 2, 5)
        psd1 = np.broadcast_to(freqs, (1, 2, 2, 5)).astype(float)
        psd0 = np.ones((1, 2, 2, 5), dtype=float)

        mock_data_group = MagicMock()
        mock_data_group.get_PSD_as_spatial_map.return_value = (
            psd0, psd1, None, 'GHz'
        )
        shift_img = np.full((1, 2, 2), 2.0)
        width_img = np.full((1, 2, 2), 0.5)

        def get_analysis_results(index):
            mock_ar = MagicMock()

            def get_image(quantity):
                if quantity == spectra_tools_module.brim.AnalysisResults.Quantity.Shift:
                    return (shift_img, None)
                if quantity == spectra_tools_module.brim.AnalysisResults.Quantity.Width:
                    return (width_img, None)
                raise ValueError("unexpected quantity")

            mock_ar.get_image.side_effect = get_image
            return mock_ar

        mock_data_group.get_analysis_results.side_effect = get_analysis_results
        mock_file = MagicMock()
        mock_file.get_data.return_value = mock_data_group

        labels_data = np.array([[[1, 1], [2, 0]]], dtype=np.uint8)
        viewer.add_labels(labels_data, name='regions')

        brim_layer = viewer.add_image(np.zeros((1, 2, 2)), name='brim_img')
        brim_layer.metadata = {
            'is_brimfile': True,
            'brimfile': mock_file,
            'Data_group': 0,
            'Analysis_result': 0,
        }
        viewer.layers.selection.active = brim_layer

        # Layer insertion events refresh the combobox based on the active
        # layer's metadata; (re-)populate it last, after all layers exist
        # and the brimfile layer is the active selection.
        widget._labels_combobox.clear()
        widget._labels_combobox.addItem('regions')
        widget._labels_combobox.setCurrentText('regions')

        widget._plot_labels_spectrum()

        # Two labels (1 and 2) should produce two rows in the summary table.
        assert widget._labels_table.rowCount() == 2
        label_values = {
            widget._labels_table.item(r, 0).text()
            for r in range(widget._labels_table.rowCount())
        }
        assert label_values == {'1', '2'}
        # Averaged spectra should have been plotted for each label.
        assert len(widget.ax_regional_spectra.lines) >= 2


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
        widget = spectra_tools_module.SpectraTools(viewer)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Basic sanity checks
        assert widget is not None
        # The widget uses raw Qt layouts rather than magicgui children,
        # so check that the native Qt widget has children.
        assert widget.native.layout().count() > 0
