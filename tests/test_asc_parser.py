"""Tests for ESRI ASCII Grid file parsing."""

import io

import numpy as np
import pytest

from src.osheightsmith.asc_parser import ASCHeader, parse_asc_file


class TestASCHeader:
    """Test ASCHeader dataclass."""

    def test_header_properties(self):
        """Test header property calculations."""
        header = ASCHeader(
            ncols=200,
            nrows=200,
            xllcorner=310000,
            yllcorner=170000,
            cellsize=50,
            nodata_value=-9999,
        )

        assert header.xllcenter == 310025  # xllcorner + cellsize/2
        assert header.yllcenter == 170025  # yllcorner + cellsize/2

    def test_header_default_nodata(self):
        """Test that nodata_value defaults to -9999."""
        header = ASCHeader(ncols=100, nrows=100, xllcorner=0, yllcorner=0, cellsize=10)
        assert header.nodata_value == -9999.0


class TestParseASCFile:
    """Test ASC file parsing."""

    def test_parse_valid_asc_file(self, sample_asc_file):
        """Test parsing a valid ASC file."""
        header, data = parse_asc_file(sample_asc_file)

        assert header.ncols == 200
        assert header.nrows == 200
        assert header.xllcorner == 310000
        assert header.yllcorner == 170000
        assert header.cellsize == 50
        assert header.nodata_value == -9999

        assert data.shape == (200, 200)
        assert data.dtype == np.float32

    def test_parse_with_xllcenter(self, sample_asc_xllcenter_content):
        """Test parsing ASC file with xllcenter/yllcenter instead of corner."""
        file_obj = io.BytesIO(sample_asc_xllcenter_content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        # Should convert xllcenter to xllcorner
        assert header.xllcorner == 310000  # 310025 - 50/2
        assert header.yllcorner == 170000  # 170025 - 50/2
        assert data.shape == (200, 200)

    def test_parse_without_nodata_value(self):
        """Test parsing ASC file without explicit nodata_value."""
        content = """ncols 10
nrows 10
xllcorner 0
yllcorner 0
cellsize 1
""" + " ".join([str(float(i)) for i in range(100)])

        file_obj = io.BytesIO(content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        assert header.nodata_value == -9999.0  # Default value
        assert data.shape == (10, 10)

    def test_parse_minimal_header(self):
        """Test parsing ASC with only required fields."""
        content = """ncols 5
nrows 5
xllcorner 100
yllcorner 200
cellsize 10
1 2 3 4 5
6 7 8 9 10
11 12 13 14 15
16 17 18 19 20
21 22 23 24 25
"""
        file_obj = io.BytesIO(content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        assert header.ncols == 5
        assert header.nrows == 5
        assert data.shape == (5, 5)
        assert data[0, 0] == 1.0
        assert data[4, 4] == 25.0

    def test_parse_with_empty_lines(self):
        """Test parsing ASC file with empty lines."""
        content = """ncols 3
nrows 3

xllcorner 0
yllcorner 0

cellsize 1

1 2 3
4 5 6
7 8 9
"""
        file_obj = io.BytesIO(content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        assert header.ncols == 3
        assert data.shape == (3, 3)

    def test_missing_required_field_ncols(self):
        """Test that missing ncols raises ValueError."""
        content = """nrows 10
xllcorner 0
yllcorner 0
cellsize 1
""" + " ".join([str(float(i)) for i in range(100)])

        file_obj = io.BytesIO(content.encode("utf-8"))
        with pytest.raises(ValueError, match="Missing required header fields.*ncols"):
            parse_asc_file(file_obj)

    def test_missing_required_field_cellsize(self):
        """Test that missing cellsize raises ValueError."""
        content = """ncols 10
nrows 10
xllcorner 0
yllcorner 0
""" + " ".join([str(float(i)) for i in range(100)])

        file_obj = io.BytesIO(content.encode("utf-8"))
        with pytest.raises(ValueError, match="Missing required header fields.*cellsize"):
            parse_asc_file(file_obj)

    def test_missing_corner_coordinates(self):
        """Test that missing corner coordinates raises ValueError."""
        content = """ncols 10
nrows 10
cellsize 1
""" + " ".join([str(float(i)) for i in range(100)])

        file_obj = io.BytesIO(content.encode("utf-8"))
        with pytest.raises(ValueError, match="Missing xllcorner/yllcorner"):
            parse_asc_file(file_obj)

    def test_data_count_mismatch_too_few(self):
        """Test that too few data values raises ValueError."""
        content = """ncols 10
nrows 10
xllcorner 0
yllcorner 0
cellsize 1
""" + " ".join([str(float(i)) for i in range(50)])  # Only 50 values instead of 100

        file_obj = io.BytesIO(content.encode("utf-8"))
        with pytest.raises(ValueError, match="Data count mismatch"):
            parse_asc_file(file_obj)

    def test_data_count_mismatch_too_many(self):
        """Test that too many data values raises ValueError."""
        content = """ncols 10
nrows 10
xllcorner 0
yllcorner 0
cellsize 1
""" + " ".join([str(float(i)) for i in range(150)])  # 150 values instead of 100

        file_obj = io.BytesIO(content.encode("utf-8"))
        with pytest.raises(ValueError, match="Data count mismatch"):
            parse_asc_file(file_obj)

    def test_no_data_section(self):
        """Test that ASC file with no data raises ValueError."""
        content = """ncols 10
nrows 10
xllcorner 0
yllcorner 0
cellsize 1
"""
        file_obj = io.BytesIO(content.encode("utf-8"))
        with pytest.raises(ValueError, match="No data found in ASC file"):
            parse_asc_file(file_obj)

    def test_parse_with_nodata_values(self):
        """Test parsing ASC file containing NODATA values."""
        content = """ncols 3
nrows 3
xllcorner 0
yllcorner 0
cellsize 1
nodata_value -9999
1 2 -9999
4 5 6
-9999 8 9
"""
        file_obj = io.BytesIO(content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        assert data[0, 2] == -9999.0
        assert data[2, 0] == -9999.0
        assert data[1, 1] == 5.0

    def test_parse_floating_point_values(self):
        """Test parsing ASC file with floating point values."""
        content = """ncols 2
nrows 2
xllcorner 0
yllcorner 0
cellsize 1
10.5 20.75
30.125 40.0625
"""
        file_obj = io.BytesIO(content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        assert data[0, 0] == pytest.approx(10.5)
        assert data[0, 1] == pytest.approx(20.75)
        assert data[1, 0] == pytest.approx(30.125)
        assert data[1, 1] == pytest.approx(40.0625)

    def test_case_insensitive_headers(self):
        """Test that header field names are case-insensitive."""
        content = """NCOLS 5
NROWS 5
XLLCORNER 0
YLLCORNER 0
CELLSIZE 1
NODATA_VALUE -9999
""" + " ".join([str(float(i)) for i in range(25)])

        file_obj = io.BytesIO(content.encode("utf-8"))
        header, data = parse_asc_file(file_obj)

        assert header.ncols == 5
        assert header.nrows == 5
        assert header.nodata_value == -9999
