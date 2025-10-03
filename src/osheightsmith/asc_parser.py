"""Parser for ESRI ASCII Grid (.asc) files."""

from dataclasses import dataclass
from typing import BinaryIO

import numpy as np


@dataclass
class ASCHeader:
    """Header information from an ESRI ASCII Grid file."""

    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata_value: float = -9999.0

    @property
    def xllcenter(self) -> float:
        """X coordinate of lower left cell center."""
        return self.xllcorner + self.cellsize / 2

    @property
    def yllcenter(self) -> float:
        """Y coordinate of lower left cell center."""
        return self.yllcorner + self.cellsize / 2


def parse_asc_file(file_obj: BinaryIO) -> tuple[ASCHeader, np.ndarray]:
    """
    Parse an ESRI ASCII Grid file.

    Args:
        file_obj: File object opened in binary mode

    Returns:
        Tuple of (header, data_array)
        data_array is a numpy array of shape (nrows, ncols)

    Raises:
        ValueError: If file format is invalid
    """
    # Read the file as text
    content = file_obj.read().decode("utf-8")
    lines = content.strip().split("\n")

    # Parse header
    header_data = {}
    data_start_line = 0

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parts = line.split(None, 1)
        if len(parts) != 2:
            # Assume we've reached the data section
            data_start_line = i
            break

        key = parts[0].lower()
        value = parts[1]

        if key in ["ncols", "nrows"]:
            header_data[key] = int(value)
        elif key in ["xllcorner", "yllcorner", "xllcenter", "yllcenter", "cellsize"]:
            header_data[key] = float(value)
        elif key == "nodata_value":
            header_data["nodata_value"] = float(value)
        else:
            # Unknown header field, assume data starts here
            data_start_line = i
            break
    else:
        raise ValueError("No data found in ASC file")

    # Validate required header fields
    required = ["ncols", "nrows", "cellsize"]
    missing = [f for f in required if f not in header_data]
    if missing:
        raise ValueError(f"Missing required header fields: {', '.join(missing)}")

    # Handle xllcorner/xllcenter and yllcorner/yllcenter
    if "xllcorner" not in header_data and "xllcenter" in header_data:
        header_data["xllcorner"] = header_data["xllcenter"] - header_data["cellsize"] / 2
    if "yllcorner" not in header_data and "yllcenter" in header_data:
        header_data["yllcorner"] = header_data["yllcenter"] - header_data["cellsize"] / 2

    if "xllcorner" not in header_data or "yllcorner" not in header_data:
        raise ValueError("Missing xllcorner/yllcorner or xllcenter/yllcenter")

    # Create header object
    header = ASCHeader(
        ncols=header_data["ncols"],
        nrows=header_data["nrows"],
        xllcorner=header_data["xllcorner"],
        yllcorner=header_data["yllcorner"],
        cellsize=header_data["cellsize"],
        nodata_value=header_data.get("nodata_value", -9999.0),
    )

    # Parse data
    data_lines = lines[data_start_line:]
    data_str = " ".join(data_lines)
    values = [float(v) for v in data_str.split()]

    expected_count = header.ncols * header.nrows
    if len(values) != expected_count:
        raise ValueError(f"Data count mismatch: expected {expected_count}, got {len(values)}")

    # Reshape into array (row 1 is at top)
    data = np.array(values, dtype=np.float32).reshape((header.nrows, header.ncols))

    return header, data


def load_asc_from_zip(zip_file, asc_path: str) -> tuple[ASCHeader, np.ndarray]:
    """
    Load an ASC file from within a zip archive.

    Args:
        zip_file: ZipFile object
        asc_path: Path to .asc file within the zip

    Returns:
        Tuple of (header, data_array)
    """
    with zip_file.open(asc_path) as f:
        return parse_asc_file(f)
