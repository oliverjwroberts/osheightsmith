"""Tests for grid reference parsing and tile calculation."""

import pytest

from src.osheightsmith.grid_reference import (
    GRID_SQUARES,
    get_tile_name,
    get_tiles_for_area,
    parse_grid_reference,
)


class TestParseGridReference:
    """Test grid reference parsing."""

    def test_parse_valid_grid_reference(self):
        """Test parsing a valid grid reference."""
        easting, northing, precision = parse_grid_reference("ST1876")
        assert easting == 318_000
        assert northing == 176_000
        assert precision == 1000

    def test_parse_with_spaces(self):
        """Test parsing grid reference with spaces."""
        easting, northing, precision = parse_grid_reference("ST 18 76")
        assert easting == 318_000
        assert northing == 176_000
        assert precision == 1000

    def test_parse_lowercase(self):
        """Test parsing lowercase grid reference."""
        easting, northing, precision = parse_grid_reference("st1876")
        assert easting == 318_000
        assert northing == 176_000

    def test_parse_high_precision(self):
        """Test parsing 10-digit grid reference (1m precision)."""
        easting, northing, precision = parse_grid_reference("ST1234567890")
        assert easting == 312_345
        assert northing == 167_890
        assert precision == 1

    def test_parse_low_precision(self):
        """Test parsing 2-digit grid reference (10km precision)."""
        easting, northing, precision = parse_grid_reference("ST17")
        assert easting == 310_000
        assert northing == 170_000
        assert precision == 10_000

    @pytest.mark.parametrize(
        "grid_ref,expected_e,expected_n",
        [
            ("SV00", 0, 0),  # Southwest corner
            ("HP55", 450_000, 1_250_000),  # Northeast corner
            ("TQ3080", 530_000, 180_000),  # London
            ("NN1234", 212_000, 734_000),  # Scottish Highlands
        ],
    )
    def test_parse_various_grid_squares(self, grid_ref, expected_e, expected_n):
        """Test parsing references from different grid squares."""
        easting, northing, precision = parse_grid_reference(grid_ref)
        assert easting == expected_e
        assert northing == expected_n

    def test_invalid_format_no_letters(self):
        """Test that grid reference with no letters raises ValueError."""
        with pytest.raises(ValueError, match="Invalid grid reference format"):
            parse_grid_reference("123456")

    def test_invalid_format_no_digits(self):
        """Test that grid reference with no digits raises ValueError."""
        with pytest.raises(ValueError, match="Invalid grid reference format"):
            parse_grid_reference("ST")

    def test_invalid_grid_square(self):
        """Test that invalid grid square code raises ValueError."""
        with pytest.raises(ValueError, match="Invalid grid square code"):
            parse_grid_reference("ZZ1234")

    def test_odd_number_of_digits(self):
        """Test that odd number of digits raises ValueError."""
        with pytest.raises(ValueError, match="even number of digits"):
            parse_grid_reference("ST123")


class TestGetTileName:
    """Test tile name generation."""

    def test_get_tile_name_basic(self):
        """Test getting tile name for basic coordinates."""
        tile = get_tile_name(318_000, 176_000)
        assert tile == "st17"

    def test_get_tile_name_boundary(self):
        """Test getting tile name at 10km boundary."""
        tile = get_tile_name(310_000, 170_000)
        assert tile == "st17"

    def test_get_tile_name_different_squares(self):
        """Test getting tile names from different grid squares."""
        assert get_tile_name(0, 0) == "sv00"
        assert get_tile_name(530_000, 180_000) == "tq38"
        assert get_tile_name(445_000, 1_205_000) == "hp40"

    def test_get_tile_name_within_square(self):
        """Test tile name calculation within a 100km square."""
        # All these should be in different tiles within ST square
        assert get_tile_name(310_000, 170_000) == "st17"
        assert get_tile_name(320_000, 170_000) == "st27"
        assert get_tile_name(310_000, 180_000) == "st18"
        assert get_tile_name(320_000, 180_000) == "st28"

    def test_invalid_coordinates(self):
        """Test that coordinates outside valid grid raise ValueError."""
        with pytest.raises(ValueError, match="outside valid grid"):
            get_tile_name(-10_000, 0)


class TestGetTilesForArea:
    """Test area tile calculation."""

    def test_single_tile_area(self):
        """Test area that fits in a single tile."""
        # 5km area centered in tile st17
        tiles = get_tiles_for_area(315_000, 175_000, 5)
        assert len(tiles) == 1
        assert "st17" in tiles

    def test_four_tile_area(self):
        """Test area that spans four tiles."""
        # 10km area centered on tile boundary
        tiles = get_tiles_for_area(315_000, 175_000, 10)
        assert len(tiles) == 4
        assert "st17" in tiles
        assert "st18" in tiles
        assert "st27" in tiles
        assert "st28" in tiles

    def test_large_area(self):
        """Test large area spanning many tiles."""
        tiles = get_tiles_for_area(315_000, 175_000, 50)
        assert len(tiles) > 4
        # Should include tiles from surrounding area

    def test_area_at_edge(self):
        """Test area at edge of grid square."""
        tiles = get_tiles_for_area(340_000, 175_000, 20)
        # Should include tiles from ST and SU squares
        assert len(tiles) >= 4

    def test_sorted_output(self):
        """Test that output tiles are sorted."""
        tiles = get_tiles_for_area(315_000, 175_000, 20)
        assert tiles == sorted(tiles)


class TestGridSquares:
    """Test GRID_SQUARES constant."""

    def test_grid_squares_coverage(self):
        """Test that all expected grid squares are present."""
        # Should have squares for England, Scotland, Wales
        assert "ST" in GRID_SQUARES  # Cardiff area
        assert "TQ" in GRID_SQUARES  # London area
        assert "NN" in GRID_SQUARES  # Scottish Highlands
        assert "SV" in GRID_SQUARES  # Southwest corner
        assert "HP" in GRID_SQUARES  # Shetland

    def test_grid_squares_unique(self):
        """Test that all grid square codes are unique."""
        codes = list(GRID_SQUARES.keys())
        assert len(codes) == len(set(codes))
