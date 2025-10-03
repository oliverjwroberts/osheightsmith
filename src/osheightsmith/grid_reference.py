"""UK Ordnance Survey grid reference parsing and conversion."""

import re
from typing import Tuple


# UK National Grid 100km square letter codes
# Each letter represents a 100km x 100km square
GRID_SQUARES = {
    "SV": (0, 0),
    "SW": (1, 0),
    "SX": (2, 0),
    "SY": (3, 0),
    "SZ": (4, 0),
    "TV": (5, 0),
    "SQ": (0, 1),
    "SR": (1, 1),
    "SS": (2, 1),
    "ST": (3, 1),
    "SU": (4, 1),
    "TQ": (5, 1),
    "TR": (6, 1),
    "SL": (0, 2),
    "SM": (1, 2),
    "SN": (2, 2),
    "SO": (3, 2),
    "SP": (4, 2),
    "TL": (5, 2),
    "TM": (6, 2),
    "SF": (0, 3),
    "SG": (1, 3),
    "SH": (2, 3),
    "SJ": (3, 3),
    "SK": (4, 3),
    "TF": (5, 3),
    "TG": (6, 3),
    "SA": (0, 4),
    "SB": (1, 4),
    "SC": (2, 4),
    "SD": (3, 4),
    "SE": (4, 4),
    "TA": (5, 4),
    "TB": (6, 4),
    "NV": (0, 5),
    "NW": (1, 5),
    "NX": (2, 5),
    "NY": (3, 5),
    "NZ": (4, 5),
    "OV": (5, 5),
    "NQ": (0, 6),
    "NR": (1, 6),
    "NS": (2, 6),
    "NT": (3, 6),
    "NU": (4, 6),
    "OQ": (5, 6),
    "NL": (0, 7),
    "NM": (1, 7),
    "NN": (2, 7),
    "NO": (3, 7),
    "NP": (4, 7),
    "OL": (5, 7),
    "NF": (0, 8),
    "NG": (1, 8),
    "NH": (2, 8),
    "NJ": (3, 8),
    "NK": (4, 8),
    "OF": (5, 8),
    "NA": (0, 9),
    "NB": (1, 9),
    "NC": (2, 9),
    "ND": (3, 9),
    "NE": (4, 9),
    "OA": (5, 9),
    "HV": (0, 10),
    "HW": (1, 10),
    "HX": (2, 10),
    "HY": (3, 10),
    "HZ": (4, 10),
    "HQ": (0, 11),
    "HR": (1, 11),
    "HS": (2, 11),
    "HT": (3, 11),
    "HU": (4, 11),
    "HL": (0, 12),
    "HM": (1, 12),
    "HN": (2, 12),
    "HO": (3, 12),
    "HP": (4, 12),
}


def parse_grid_reference(grid_ref: str) -> Tuple[int, int, int]:
    """
    Parse a UK grid reference into easting, northing coordinates.

    Args:
        grid_ref: Grid reference like "ST1876" or "ST 18 76"

    Returns:
        Tuple of (easting, northing, precision) in meters
        precision is the resolution of the grid reference (e.g., 1000m for 4 digits)

    Raises:
        ValueError: If grid reference format is invalid
    """
    # Remove spaces and convert to uppercase
    grid_ref = grid_ref.replace(" ", "").upper()

    # Match pattern: 2 letters followed by even number of digits
    match = re.match(r"^([A-Z]{2})(\d+)$", grid_ref)
    if not match:
        raise ValueError(f"Invalid grid reference format: {grid_ref}")

    square, digits = match.groups()

    # Check if square code is valid
    if square not in GRID_SQUARES:
        raise ValueError(f"Invalid grid square code: {square}")

    # Digits must be even (equal easting and northing digits)
    if len(digits) % 2 != 0:
        raise ValueError(f"Grid reference must have even number of digits, got {len(digits)}")

    # Split into easting and northing
    half = len(digits) // 2
    easting_digits = digits[:half]
    northing_digits = digits[half:]

    # Get 100km square offset
    square_e, square_n = GRID_SQUARES[square]

    # Calculate precision (resolution)
    precision = 10 ** (5 - half)  # 5 digits = 1m, 4 = 10m, 3 = 100m, etc.

    # Calculate full coordinates
    easting = square_e * 100000 + int(easting_digits) * precision
    northing = square_n * 100000 + int(northing_digits) * precision

    return easting, northing, precision


def get_tile_name(easting: int, northing: int) -> str:
    """
    Get the OS Terrain 50 tile name for given coordinates.

    Tiles are 10km x 10km squares named like "st17" (lowercase).

    Args:
        easting: Easting coordinate in meters
        northing: Northing coordinate in meters

    Returns:
        Tile name like "st17"
    """
    # Find 100km square
    square_e = easting // 100000
    square_n = northing // 100000

    # Find the square code
    square_code = None
    for code, (e, n) in GRID_SQUARES.items():
        if e == square_e and n == square_n:
            square_code = code.lower()
            break

    if not square_code:
        raise ValueError(f"Coordinates outside valid grid: {easting}, {northing}")

    # Calculate 10km tile within the 100km square
    tile_e = (easting % 100000) // 10000
    tile_n = (northing % 100000) // 10000

    return f"{square_code}{tile_e}{tile_n}"


def get_tiles_for_area(center_e: int, center_n: int, size_km: int) -> list[str]:
    """
    Get list of tile names needed to cover an area.

    Args:
        center_e: Center easting in meters
        center_n: Center northing in meters
        size_km: Size of square area in kilometers

    Returns:
        List of tile names needed to cover the area
    """
    size_m = size_km * 1000
    half_size = size_m // 2

    # Calculate bounds
    min_e = center_e - half_size
    max_e = center_e + half_size
    min_n = center_n - half_size
    max_n = center_n + half_size

    # Get all tiles that intersect this area
    tiles = set()

    # Round to tile boundaries (10km)
    start_e = (min_e // 10000) * 10000
    end_e = ((max_e // 10000) + 1) * 10000
    start_n = (min_n // 10000) * 10000
    end_n = ((max_n // 10000) + 1) * 10000

    for e in range(start_e, end_e, 10000):
        for n in range(start_n, end_n, 10000):
            try:
                tiles.add(get_tile_name(e, n))
            except ValueError:
                # Skip tiles outside valid grid
                continue

    return sorted(list(tiles))
