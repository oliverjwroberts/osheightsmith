"""Shared pytest fixtures for OSHeightsmith tests."""

import io
from typing import BinaryIO

import numpy as np
import pytest


@pytest.fixture
def sample_asc_content() -> str:
    """Sample ESRI ASCII Grid file content."""
    return """ncols 200
nrows 200
xllcorner 310000
yllcorner 170000
cellsize 50
nodata_value -9999
10.5 11.2 12.3 13.4 14.5 15.6 16.7 17.8 18.9 19.0
20.1 21.2 22.3 23.4 24.5 25.6 26.7 27.8 28.9 29.0
""" + " ".join([str(float(i)) for i in range(39980)])  # Fill remaining cells to reach 200x200


@pytest.fixture
def sample_asc_file(sample_asc_content: str) -> BinaryIO:
    """Sample ESRI ASCII Grid file as a binary file object."""
    return io.BytesIO(sample_asc_content.encode("utf-8"))


@pytest.fixture
def sample_asc_xllcenter_content() -> str:
    """Sample ASC content using xllcenter/yllcenter instead of xllcorner/yllcorner."""
    return """ncols 200
nrows 200
xllcenter 310025
yllcenter 170025
cellsize 50
nodata_value -9999
""" + " ".join([str(float(i)) for i in range(40000)])


@pytest.fixture
def sample_heightmap_data() -> np.ndarray:
    """Sample heightmap array for testing."""
    # Create a 100x100 array with gradient values
    data = np.zeros((100, 100), dtype=np.float32)
    for i in range(100):
        for j in range(100):
            data[i, j] = i * 100 + j
    return data


@pytest.fixture
def sample_heightmap_with_nodata() -> np.ndarray:
    """Sample heightmap with NODATA values."""
    data = np.full((100, 100), 100.0, dtype=np.float32)
    # Add some NODATA values
    data[0:10, 0:10] = -9999.0
    data[90:100, 90:100] = -9999.0
    return data


@pytest.fixture
def mock_tile_data():
    """Mock tile data for testing heightmap stitching."""
    from src.osheightsmith.asc_parser import ASCHeader

    # Create two 200x200 tiles side by side
    header1 = ASCHeader(
        ncols=200, nrows=200, xllcorner=310000, yllcorner=170000, cellsize=50, nodata_value=-9999
    )
    data1 = np.random.rand(200, 200).astype(np.float32) * 100

    header2 = ASCHeader(
        ncols=200, nrows=200, xllcorner=320000, yllcorner=170000, cellsize=50, nodata_value=-9999
    )
    data2 = np.random.rand(200, 200).astype(np.float32) * 100

    return {
        "st17": (header1, data1),
        "st27": (header2, data2),
    }
