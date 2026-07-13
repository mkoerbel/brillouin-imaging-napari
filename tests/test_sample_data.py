"""Tests for the sample data module."""
from unittest.mock import patch
from brillouin_imaging._sample_data import (
    load_sample_data,
    sample_data_drosophila,
    sample_data_zfeye,
    sample_data_zfSBS,
    sample_data_beadsFTBM,
)


class TestLoadSampleData:
    """Tests for load_sample_data function."""

    @patch('brillouin_imaging._sample_data.reader_function')
    def test_load_sample_data_calls_reader_function(self, mock_reader):
        """Test that load_sample_data calls reader_function with url."""
        url = "https://example.com/test.brim.zarr"
        
        result = load_sample_data(url)
        
        # Verify reader_function was called with the url
        mock_reader.assert_called_once_with(url)
        
        # Verify the return value
        assert result == [(None,)]

    @patch('brillouin_imaging._sample_data.reader_function')
    def test_load_sample_data_with_different_url(self, mock_reader):
        """Test load_sample_data with a different url."""
        url = "https://different.com/data.brim.zarr"
        
        result = load_sample_data(url)
        
        mock_reader.assert_called_once_with(url)
        assert result == [(None,)]


class TestSampleDataFunctions:
    """Tests for individual sample data functions."""

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_drosophila(self, mock_load):
        """Test sample_data_drosophila uses the EMBL URL."""
        sample_data_drosophila()

        mock_load.assert_called_once_with(
            'https://s3.embl.de/brim-example-files/drosophila_LSBM.brim.zarr'
        )

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_zfeye(self, mock_load):
        """Test sample_data_zfeye uses the EMBL URL."""
        sample_data_zfeye()

        mock_load.assert_called_once_with(
            'https://s3.embl.de/brim-example-files/zebrafish_eye_confocal.brim.zarr'
        )

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_zfSBS(self, mock_load):
        """Test sample_data_zfSBS uses the EMBL URL."""
        sample_data_zfSBS()

        mock_load.assert_called_once_with(
            'https://s3.embl.de/brim-example-files/zebrafish_ECM_SBS.brim.zarr'
        )

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_beadsFTBM(self, mock_load):
        """Test sample_data_beadsFTBM uses the EMBL URL."""
        sample_data_beadsFTBM()

        mock_load.assert_called_once_with(
            'https://s3.embl.de/brim-example-files/oil_beads_FTBM.brim.zarr'
        )