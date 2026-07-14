"""Tests for the reader module."""
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np
import brimfile as brim
from brillouin_imaging._reader import (
    napari_get_reader,
    reader_function,
    create_brim_widget,
)


class TestNapariGetReader:
    """Tests for napari_get_reader function."""

    def test_returns_none_for_list_of_paths(self):
        """Test that napari_get_reader returns None for list of paths."""
        paths = ["file1.brim.zarr", "file2.brim.zarr"]
        result = napari_get_reader(paths)
        assert result is None

    def test_returns_none_for_invalid_extension(self):
        """Test that napari_get_reader returns None for invalid extension."""
        result = napari_get_reader("file.txt")
        assert result is None

    def test_returns_none_for_nonexistent_zarr_directory(self):
        """Test that napari_get_reader returns None for non-existent zarr directory."""
        result = napari_get_reader("nonexistent.brim.zarr")
        assert result is None

    @patch('brillouin_imaging._reader.brim.File')
    def test_returns_reader_function_for_valid_zarr(self, mock_brim_file, tmp_path):
        """Test that napari_get_reader returns reader function for valid zarr."""
        # Create a temporary directory to simulate a zarr file
        zarr_path = tmp_path / "test.brim.zarr"
        zarr_path.mkdir()
        
        # Mock the brim.File to not raise an exception
        mock_brim_file.return_value = MagicMock()
        
        result = napari_get_reader(str(zarr_path))
        assert result is not None
        assert result == reader_function

    @patch('brillouin_imaging._reader.brim.File')
    def test_returns_reader_function_for_valid_zip(self, mock_brim_file, tmp_path):
        """Test that napari_get_reader returns reader function for valid zip."""
        # Create a temporary zip file
        zip_path = tmp_path / "test.brim.zip"
        zip_path.touch()
        
        # Mock the brim.File to not raise an exception
        mock_brim_file.return_value = MagicMock()
        
        result = napari_get_reader(str(zip_path))
        assert result is not None
        assert result == reader_function

    @patch('brillouin_imaging._reader.brim.File')
    def test_returns_none_when_brim_file_raises_exception(self, mock_brim_file, tmp_path):
        """Test that napari_get_reader returns None when brim.File raises exception."""
        # Create a temporary zip file
        zip_path = tmp_path / "test.brim.zip"
        zip_path.touch()
        
        # Mock the brim.File to raise an exception
        mock_brim_file.side_effect = Exception("Cannot read file")
        
        result = napari_get_reader(str(zip_path))
        assert result is None


class TestReaderFunction:
    """Tests for reader_function.
    
    Note: These tests use mocking because testing with a real napari viewer
    requires actual brim files and full Qt environment setup.
    """

    @patch('brillouin_imaging._reader.napari.current_viewer')
    @patch('brillouin_imaging._reader.brim.File')
    @patch('brillouin_imaging._reader.create_brim_widget')
    def test_reader_function_returns_none_tuple(
        self, mock_create_widget, mock_brim_file, mock_viewer
    ):
        """Test that reader_function returns a tuple with None."""
        # Setup mocks
        mock_file = MagicMock()
        mock_brim_file.return_value = mock_file
        
        mock_widget = MagicMock()
        mock_create_widget.return_value = mock_widget
        
        mock_dock = MagicMock()
        mock_viewer_instance = MagicMock()
        mock_viewer_instance.window.add_dock_widget.return_value = mock_dock
        mock_viewer.return_value = mock_viewer_instance
        
        # Call the function
        result = reader_function("test.brim.zarr")
        
        # Verify the result
        assert result == [(None,)]
        
        # Verify that the widget was created and added
        mock_create_widget.assert_called_once_with(mock_file)
        mock_viewer_instance.window.add_dock_widget.assert_called_once()

    @patch('brillouin_imaging._reader.napari.current_viewer')
    @patch('brillouin_imaging._reader.brim.File')
    @patch('brillouin_imaging._reader.create_brim_widget')
    def test_reader_function_connects_close_callback(
        self, mock_create_widget, mock_brim_file, mock_viewer
    ):
        """Test that reader_function connects close callback to widget."""
        # Setup mocks
        mock_file = MagicMock()
        mock_brim_file.return_value = mock_file
        
        mock_widget = MagicMock()
        mock_create_widget.return_value = mock_widget
        
        mock_dock = MagicMock()
        mock_viewer_instance = MagicMock()
        mock_viewer_instance.window.add_dock_widget.return_value = mock_dock
        mock_viewer.return_value = mock_viewer_instance
        
        # Call the function
        reader_function("test.brim.zarr")
        
        # Verify that the close callback was connected
        mock_dock.destroyed.connect.assert_called_once()


class TestCreateBrimWidget:
    """Tests for create_brim_widget function."""

    @pytest.mark.qt
    def test_create_brim_widget_returns_container(self, qtbot):
        """Test that create_brim_widget returns a Container."""
        from magicgui.widgets import Container
        
        # Create a mock file object
        mock_file = MagicMock()
        mock_file.list_data_groups.return_value = [
            {'custom_name': 'Data Group 1', 'index': 0}
        ]
        
        # Call the function
        widget = create_brim_widget(mock_file)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify the result
        assert isinstance(widget, Container)

    @pytest.mark.qt
    def test_create_brim_widget_has_expected_widgets(self, qtbot):
        """Test that create_brim_widget creates expected widgets."""
        # Create a mock file object
        mock_file = MagicMock()
        mock_file.list_data_groups.return_value = [
            {'custom_name': 'Data Group 1', 'index': 0},
            {'custom_name': 'Data Group 2', 'index': 1}
        ]
        
        # Call the function
        widget = create_brim_widget(mock_file)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Verify the widget has the expected components
        assert len(widget) == 7  # 1 label + 4 combo boxes + 2 buttons
        assert hasattr(widget, 'data_groups')
        
    @pytest.mark.qt
    def test_create_brim_widget_initializes_combo_boxes(self, qtbot):
        """Test that create_brim_widget initializes combo boxes with data."""
        # Create a mock file object
        mock_file = MagicMock()
        mock_file.list_data_groups.return_value = [
            {'custom_name': 'Data Group 1', 'index': 0},
            {'custom_name': 'Data Group 2', 'index': 1}
        ]
        
        # Call the function
        widget = create_brim_widget(mock_file)
        
        # Add widget to qtbot for proper cleanup (napari guideline)
        qtbot.addWidget(widget.native)
        
        # Check that data_groups combo box has the right choices
        data_combo = widget[1]  # First widget should be data_groups
        assert len(data_combo.choices) == 2
        assert 'Data Group 1' in data_combo.choices
        assert 'Data Group 2' in data_combo.choices


def _make_mock_brim_file():
    """Build a mock ``brim.File`` with a single data group / analysis result.

    The analysis result exposes both AntiStokes and Stokes quantities so
    that the full ``on_data_change`` -> ``on_analysis_results_change`` ->
    ``on_quantity_change`` callback chain can be exercised.
    """
    pt_cls = brim.Data.AnalysisResults.PeakType
    q_shift = brim.Data.AnalysisResults.Quantity.Shift
    q_width = brim.Data.AnalysisResults.Quantity.Width

    mock_ar = MagicMock()
    mock_ar.list_existing_quantities.side_effect = (
        lambda peak_type: [q_shift, q_width]
    )
    mock_ar.list_existing_peak_types.return_value = [
        pt_cls.AntiStokes,
        pt_cls.Stokes,
    ]

    px_size_x = MagicMock()
    px_size_x.value = 0.5
    px_size_x.units = 'um'
    px_size_y = MagicMock()
    px_size_y.value = 0.5
    px_size_y.units = 'um'
    mock_ar.get_image.return_value = (
        np.zeros((4, 5)),  # image data
        [px_size_x, px_size_y],
    )

    mock_data = MagicMock()
    mock_data.list_AnalysisResults.return_value = [
        {'custom_name': 'Analysis Result 1', 'index': 0}
    ]
    mock_data.get_analysis_results.return_value = mock_ar
    mock_data.get_index.return_value = 0

    mock_file = MagicMock()
    mock_file.filename = 'test.brim.zip'
    mock_file.list_data_groups.return_value = [
        {'custom_name': 'Data Group 1', 'index': 0}
    ]
    mock_file.get_data.return_value = mock_data

    return mock_file, mock_data, mock_ar


class TestCreateBrimWidgetCallbacks:
    """Tests for the internal callback chain of create_brim_widget."""

    @pytest.mark.qt
    def test_data_change_populates_analysis_results_and_quantities(
        self, qtbot
    ):
        """Selecting a data group should populate downstream combo boxes."""
        mock_file, mock_data, mock_ar = _make_mock_brim_file()

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)

        analysis_results_combo = widget[2]
        quantity_combo = widget[3]
        peak_types_combo = widget[4]

        # Triggering the data combo change should cascade through the
        # analysis-results and quantity handlers.
        widget.data_groups.changed.emit(None)

        assert list(analysis_results_combo.choices) == [
            'Analysis Result 1'
        ]
        assert analysis_results_combo.value == 'Analysis Result 1'
        quantity_choices = [str(q) for q in quantity_combo.choices]
        assert str(brim.Data.AnalysisResults.Quantity.Shift) in quantity_choices
        assert str(brim.Data.AnalysisResults.Quantity.Width) in quantity_choices
        # Both peak types exist, so all three peak-type choices are shown.
        assert list(peak_types_combo.choices) == [
            'average', 'AntiStokes', 'Stokes'
        ]

    @pytest.mark.qt
    def test_quantity_change_single_antistokes_peak_type(self, qtbot):
        """When only AntiStokes exists, only that peak type is selectable."""
        mock_file, mock_data, mock_ar = _make_mock_brim_file()
        pt_cls = brim.Data.AnalysisResults.PeakType
        mock_ar.list_existing_peak_types.return_value = [pt_cls.AntiStokes]

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)
        peak_types_combo = widget[4]

        widget.data_groups.changed.emit(None)

        assert list(peak_types_combo.choices) == ['AntiStokes']
        assert peak_types_combo.value == 'AntiStokes'

    @pytest.mark.qt
    def test_quantity_change_single_stokes_peak_type(self, qtbot):
        """When only Stokes exists, only that peak type is selectable."""
        mock_file, mock_data, mock_ar = _make_mock_brim_file()
        pt_cls = brim.Data.AnalysisResults.PeakType
        mock_ar.list_existing_peak_types.return_value = [pt_cls.Stokes]

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)
        peak_types_combo = widget[4]

        widget.data_groups.changed.emit(None)

        assert list(peak_types_combo.choices) == ['Stokes']
        assert peak_types_combo.value == 'Stokes'

    @pytest.mark.qt
    @pytest.mark.qt_no_exception_capture
    def test_quantity_change_raises_for_invalid_peak_type(self, qtbot):
        """A single, unrecognized peak type should raise ValueError."""
        from psygnal._exceptions import EmitLoopError

        mock_file, mock_data, mock_ar = _make_mock_brim_file()
        mock_ar.list_existing_peak_types.return_value = ['not_a_peak_type']

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)

        with pytest.raises(EmitLoopError) as excinfo:
            widget.data_groups.changed.emit(None)

        assert isinstance(excinfo.value.__cause__, ValueError)
        assert "not a valid PeakType" in str(excinfo.value.__cause__)

    @pytest.mark.qt
    @patch('brillouin_imaging._reader.napari.current_viewer')
    def test_add_image_button_adds_layer_for_average_peak_type(
        self, mock_current_viewer, qtbot
    ):
        """Clicking 'Add image' should add a layer using the average peak type."""
        mock_file, mock_data, mock_ar = _make_mock_brim_file()
        mock_viewer_instance = MagicMock()
        mock_current_viewer.return_value = mock_viewer_instance

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)

        widget.data_groups.changed.emit(None)
        peak_types_combo = widget[4]
        assert peak_types_combo.value == 'average'

        add_image_btn = widget[5]
        add_image_btn.clicked.emit()

        mock_ar.get_image.assert_called()
        mock_viewer_instance.add_layer.assert_called_once()
        # Called with pt_cls.average as the second positional argument.
        args, kwargs = mock_ar.get_image.call_args
        assert args[1] == brim.Data.AnalysisResults.PeakType.average

    @pytest.mark.qt
    @patch('brillouin_imaging._reader.napari.current_viewer')
    def test_add_image_button_recovers_on_missing_analysis_results(
        self, mock_current_viewer, qtbot
    ):
        """If get_analysis_results raises, the widget attempts to reset.

        Note: the current implementation's recovery path
        (``on_data_change`` -> ``on_analysis_results_change``) calls
        ``get_analysis_results`` again without a try/except, so if the
        failure persists the recovery itself raises. This is a
        pre-existing fragility in ``_reader.py`` not fixed here; the test
        uses ``qtbot.captureExceptions`` to document the current behavior
        without letting it fail the whole test session.
        """
        mock_file, mock_data, mock_ar = _make_mock_brim_file()
        mock_current_viewer.return_value = MagicMock()

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)
        widget.data_groups.changed.emit(None)

        mock_data.get_analysis_results.side_effect = Exception(
            "analysis results no longer available"
        )

        add_image_btn = widget[5]
        from psygnal._exceptions import EmitLoopError
        with pytest.raises(EmitLoopError) as excinfo:
            add_image_btn.clicked.emit()

        # The first failure is swallowed by the bare except in
        # on_add_image_btn_pressed; the retry inside on_data_change's
        # cascade is not guarded and surfaces here.
        assert isinstance(excinfo.value.__cause__, Exception)

    @pytest.mark.qt
    @patch('brillouin_imaging._reader.napari.current_viewer')
    def test_reset_button_reinitializes_widget(
        self, mock_current_viewer, qtbot
    ):
        """The Reset button should re-run on_data_change."""
        mock_file, mock_data, mock_ar = _make_mock_brim_file()
        mock_current_viewer.return_value = MagicMock()

        widget = create_brim_widget(mock_file)
        qtbot.addWidget(widget.native)
        widget.data_groups.changed.emit(None)

        analysis_results_combo = widget[2]
        call_count_before = mock_data.list_AnalysisResults.call_count

        reset_btn = widget[6]
        reset_btn.clicked.emit()

        assert (
            mock_data.list_AnalysisResults.call_count
            == call_count_before + 1
        )
        assert analysis_results_combo.value == 'Analysis Result 1'
