"""Tests for heightmap generation and stitching."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from src.osheightsmith.asc_parser import ASCHeader
from src.osheightsmith.heightmap import HeightmapGenerator


class TestHeightmapGenerator:
    """Test HeightmapGenerator class."""

    def test_init_with_valid_path(self, tmp_path):
        """Test initializing generator with valid zip path."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        generator = HeightmapGenerator(str(zip_path))
        assert generator.terrain_zip_path == zip_path

    def test_init_with_missing_file(self):
        """Test that initializing with missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Terrain data not found"):
            HeightmapGenerator("nonexistent.zip")


class TestStitchTiles:
    """Test tile stitching functionality."""

    def test_stitch_single_tile(self):
        """Test stitching a single tile."""
        # Create a simple tile
        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data = np.arange(40000, dtype=np.float32).reshape(200, 200)

        tile_data = {"st17": (header, data)}

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._stitch_tiles(tile_data, 315000, 175000, 10)

        # Result should be a subset of the original tile
        assert result.shape[0] > 0
        assert result.shape[1] > 0

    def test_stitch_multiple_tiles(self):
        """Test stitching multiple tiles together."""
        # Create two tiles side by side
        header1 = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data1 = np.ones((200, 200), dtype=np.float32) * 100

        header2 = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=320000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data2 = np.ones((200, 200), dtype=np.float32) * 200

        tile_data = {
            "st17": (header1, data1),
            "st27": (header2, data2),
        }

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._stitch_tiles(tile_data, 315000, 175000, 10)

        # Should have stitched tiles together
        assert result.shape[0] > 0
        assert result.shape[1] > 0

    def test_stitch_tiles_with_nodata(self):
        """Test stitching tiles containing NODATA values."""
        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data = np.full((200, 200), 100.0, dtype=np.float32)
        data[0:10, 0:10] = -9999.0  # Add NODATA region

        tile_data = {"st17": (header, data)}

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._stitch_tiles(tile_data, 315000, 175000, 10)

        # Should preserve NODATA values
        assert -9999.0 in result


class TestNormaliseHeightmap:
    """Test heightmap normalization."""

    def test_normalise_to_8bit(self):
        """Test normalising heightmap to 8-bit."""
        data = np.array([[0, 50, 100], [150, 200, 250]], dtype=np.float32)

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._normalise_heightmap(data, 8)

        assert result.dtype == np.uint8
        assert result.min() == 0
        assert result.max() == 255

    def test_normalise_to_16bit(self):
        """Test normalising heightmap to 16-bit."""
        data = np.array([[0, 500, 1000], [1500, 2000, 2500]], dtype=np.float32)

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._normalise_heightmap(data, 16)

        assert result.dtype == np.uint16
        assert result.min() == 0
        assert result.max() == 65535

    def test_normalise_with_nodata(self):
        """Test normalising heightmap with NODATA values."""
        # Create heightmap with varying values and NODATA
        data = np.arange(10000, dtype=np.float32).reshape(100, 100)
        data[0:10, 0:10] = -9999.0  # NODATA region
        data[90:100, 90:100] = -9999.0  # NODATA region

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._normalise_heightmap(data, 8)

        # NODATA values should be set to 0
        assert result[0, 0] == 0
        assert result[95, 95] == 0

        # Valid data should be normalised
        assert result[50, 50] > 0

    def test_normalise_all_nodata(self):
        """Test normalising heightmap with all NODATA values."""
        data = np.full((100, 100), -9999.0, dtype=np.float32)

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._normalise_heightmap(data, 8)

        # Should return all zeros
        assert np.all(result == 0)

    def test_normalise_uniform_values(self):
        """Test normalising heightmap with uniform values (no range)."""
        data = np.full((100, 100), 100.0, dtype=np.float32)

        generator = HeightmapGenerator.__new__(HeightmapGenerator)
        result = generator._normalise_heightmap(data, 8)

        # Should return all zeros when there's no range
        assert np.all(result == 0)


class TestGenerateHeightmap:
    """Test end-to-end heightmap generation."""

    @patch.object(HeightmapGenerator, "_load_tile")
    def test_generate_heightmap_basic(self, mock_load_tile, tmp_path):
        """Test basic heightmap generation with mocked tile loading."""
        # Create a temporary zip file
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        # Mock tile data
        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data = np.random.rand(200, 200).astype(np.float32) * 100

        mock_load_tile.return_value = (header, data)

        generator = HeightmapGenerator(str(zip_path))

        # Generate heightmap
        output_path = tmp_path / "output.png"
        result_path, width, height = generator.generate_heightmap(
            "ST1876", 10, str(output_path), bit_depth=8
        )

        assert Path(result_path).exists()
        assert width > 0
        assert height > 0

        # Verify it's a valid PNG
        img = Image.open(result_path)
        assert img.mode == "L"  # Grayscale

    @patch.object(HeightmapGenerator, "_load_tile")
    def test_generate_heightmap_16bit(self, mock_load_tile, tmp_path):
        """Test generating 16-bit heightmap."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data = np.random.rand(200, 200).astype(np.float32) * 1000

        mock_load_tile.return_value = (header, data)

        generator = HeightmapGenerator(str(zip_path))

        output_path = tmp_path / "output16.png"
        result_path, width, height = generator.generate_heightmap(
            "ST1876", 10, str(output_path), bit_depth=16
        )

        assert Path(result_path).exists()

        # Verify it's a valid 16-bit PNG
        img = Image.open(result_path)
        assert img.mode == "I;16"  # 16-bit integer mode

    @patch.object(HeightmapGenerator, "_load_tile")
    def test_generate_heightmap_auto_filename(self, mock_load_tile, tmp_path):
        """Test auto-generating output filename."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data = np.random.rand(200, 200).astype(np.float32) * 100

        mock_load_tile.return_value = (header, data)

        generator = HeightmapGenerator(str(zip_path))

        result_path, _, _ = generator.generate_heightmap("ST1876", 10, bit_depth=8)

        # Should auto-generate filename
        assert "st1876" in result_path.lower()
        assert "10km" in result_path.lower()
        assert result_path.endswith(".png")

    @patch.object(HeightmapGenerator, "_load_tile")
    def test_generate_heightmap_no_tiles(self, mock_load_tile, tmp_path):
        """Test that generating heightmap with no tile data raises error."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        mock_load_tile.return_value = None  # No tile found

        generator = HeightmapGenerator(str(zip_path))

        with pytest.raises(FileNotFoundError, match="No terrain data found"):
            generator.generate_heightmap("ST1876", 10, bit_depth=8)

    def test_invalid_bit_depth(self, tmp_path):
        """Test that invalid bit depth raises ValueError."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        generator = HeightmapGenerator(str(zip_path))

        with pytest.raises(ValueError, match="bit_depth must be 8 or 16"):
            generator.generate_heightmap("ST1876", 10, bit_depth=32)

    @patch.object(HeightmapGenerator, "_load_tile")
    def test_generate_with_missing_tiles_filled(self, mock_load_tile, tmp_path):
        """Test generating heightmap with missing tiles filled with zeros."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )
        data = np.random.rand(200, 200).astype(np.float32) * 100

        # Simulate some tiles being missing (return None)
        def load_tile_side_effect(tile_name, fill_missing=False):
            if tile_name == "st17":
                return (header, data)
            elif fill_missing:
                # Return zero-filled placeholder
                from src.osheightsmith.grid_reference import get_tile_corner

                xllcorner, yllcorner = get_tile_corner(tile_name)
                placeholder_header = ASCHeader(
                    ncols=200,
                    nrows=200,
                    xllcorner=xllcorner,
                    yllcorner=yllcorner,
                    cellsize=50,
                    nodata_value=-9999,
                )
                return (placeholder_header, np.zeros((200, 200), dtype=np.float32))
            else:
                return None

        mock_load_tile.side_effect = load_tile_side_effect

        generator = HeightmapGenerator(str(zip_path))

        output_path = tmp_path / "output_with_fill.png"
        result_path, width, height = generator.generate_heightmap(
            "ST1876", 10, str(output_path), bit_depth=8, fill_missing=True
        )

        assert Path(result_path).exists()
        # Should have called _load_tile with fill_missing=True
        assert mock_load_tile.call_count >= 1
