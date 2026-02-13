"""Tests for the sample data module."""
from unittest.mock import patch, MagicMock
import pytest
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
    def test_sample_data_drosophila_embl(self, mock_load):
        """Test sample_data_drosophila with EMBL URL."""
        # Ensure load_from_EMBL is True (default)
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = True
        
        try:
            sample_data_drosophila()
            
            # Verify it was called with EMBL URL
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 's3.embl.de' in call_args
            assert 'drosophila_LSBM.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_drosophila_gcs(self, mock_load):
        """Test sample_data_drosophila with Google Cloud Storage URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = False
        
        try:
            sample_data_drosophila()
            
            # Verify it was called with GCS URL
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 'storage.googleapis.com' in call_args
            assert 'drosophila_LSBM.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_zfeye_embl(self, mock_load):
        """Test sample_data_zfeye with EMBL URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = True
        
        try:
            sample_data_zfeye()
            
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 's3.embl.de' in call_args
            assert 'zebrafish_eye_confocal.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_zfeye_gcs(self, mock_load):
        """Test sample_data_zfeye with Google Cloud Storage URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = False
        
        try:
            sample_data_zfeye()
            
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 'storage.googleapis.com' in call_args
            assert 'zebrafish_eye_confocal.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_zfSBS_embl(self, mock_load):
        """Test sample_data_zfSBS with EMBL URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = True
        
        try:
            sample_data_zfSBS()
            
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 's3.embl.de' in call_args
            assert 'zebrafish_ECM_SBS.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_zfSBS_gcs(self, mock_load):
        """Test sample_data_zfSBS with Google Cloud Storage URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = False
        
        try:
            sample_data_zfSBS()
            
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 'storage.googleapis.com' in call_args
            assert 'zebrafish_ECM_SBS.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_beadsFTBM_embl(self, mock_load):
        """Test sample_data_beadsFTBM with EMBL URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = True
        
        try:
            sample_data_beadsFTBM()
            
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 's3.embl.de' in call_args
            assert 'oil_beads_FTBM.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value

    @patch('brillouin_imaging._sample_data.load_sample_data')
    def test_sample_data_beadsFTBM_gcs(self, mock_load):
        """Test sample_data_beadsFTBM with Google Cloud Storage URL."""
        import brillouin_imaging._sample_data as sd
        original_value = sd.load_from_EMBL
        sd.load_from_EMBL = False
        
        try:
            sample_data_beadsFTBM()
            
            mock_load.assert_called_once()
            call_args = mock_load.call_args[0][0]
            assert 'storage.googleapis.com' in call_args
            assert 'oil_beads_FTBM.brim.zarr' in call_args
        finally:
            sd.load_from_EMBL = original_value