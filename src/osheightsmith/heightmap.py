"""Heightmap generation from OS Terrain 50 data."""

import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .asc_parser import ASCHeader, load_asc_from_zip
from .grid_reference import get_tiles_for_area, parse_grid_reference


class HeightmapGenerator:
    """Generate PNG heightmaps from OS Terrain 50 data."""

    def __init__(self, terrain_zip_path: str):
        """
        Initialize the generator.

        Args:
            terrain_zip_path: Path to the OS Terrain 50 zip file
        """
        self.terrain_zip_path = Path(terrain_zip_path)
        if not self.terrain_zip_path.exists():
            raise FileNotFoundError(f"Terrain data not found: {terrain_zip_path}")

    def _load_tile(self, tile_name: str) -> Optional[tuple[ASCHeader, np.ndarray]]:
        """
        Load a single tile from the nested zip structure.

        Args:
            tile_name: Tile name like "st17"

        Returns:
            Tuple of (header, data) or None if tile not found
        """
        # Tile structure: data/{grid_square}/{tile}_OST50GRID_20250529.zip
        # Inside that zip: {tile}_OST50GRID_20250529.asc
        grid_square = tile_name[:2]

        # Open the main zip
        with zipfile.ZipFile(self.terrain_zip_path, "r") as main_zip:
            # Look for the tile zip
            tile_zip_pattern = f"data/{grid_square}/{tile_name}_OST50GRID_"

            # Find matching tile zip
            tile_zip_name = None
            for name in main_zip.namelist():
                if name.startswith(tile_zip_pattern) and name.endswith(".zip"):
                    tile_zip_name = name
                    break

            if not tile_zip_name:
                return None

            # Read the nested zip
            with main_zip.open(tile_zip_name) as tile_zip_file:
                tile_zip_data = BytesIO(tile_zip_file.read())

                with zipfile.ZipFile(tile_zip_data, "r") as tile_zip:
                    # Find the .asc file
                    asc_files = [f for f in tile_zip.namelist() if f.endswith(".asc")]
                    if not asc_files:
                        return None

                    return load_asc_from_zip(tile_zip, asc_files[0])

    def generate_heightmap(
        self,
        grid_ref: str,
        size_km: int,
        output_path: Optional[str] = None,
        bit_depth: int = 8,
    ) -> tuple[str, int, int]:
        """
        Generate a square heightmap from a grid reference.

        Args:
            grid_ref: UK grid reference (e.g., "ST1876")
            size_km: Size of the area in kilometers
            output_path: Output PNG path (default: auto-generated)
            bit_depth: Bit depth for PNG (8 or 16)

        Returns:
            Tuple of (output_path, width, height)

        Raises:
            ValueError: If parameters are invalid
            FileNotFoundError: If required tiles are not found
        """
        if bit_depth not in [8, 16]:
            raise ValueError("bit_depth must be 8 or 16")

        # Parse grid reference
        center_e, center_n, precision = parse_grid_reference(grid_ref)

        # Get required tiles
        tiles = get_tiles_for_area(center_e, center_n, size_km)
        if not tiles:
            raise ValueError(f"No tiles found for grid reference {grid_ref}")

        # Load all tiles
        tile_data = {}
        for tile_name in tiles:
            data = self._load_tile(tile_name)
            if data:
                tile_data[tile_name] = data

        if not tile_data:
            raise FileNotFoundError(f"No terrain data found for area {grid_ref}")

        # Stitch tiles together
        heightmap = self._stitch_tiles(tile_data, center_e, center_n, size_km)

        # Normalise to output bit depth
        heightmap = self._normalise_heightmap(heightmap, bit_depth)

        # Generate output filename if not provided
        if output_path is None:
            output_path = f"heightmaps/{grid_ref.lower()}_{size_km}km.png"

        # Ensure the heightmaps directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save as PNG
        if bit_depth == 8:
            img = Image.fromarray(heightmap.astype(np.uint8), mode="L")
        else:
            img = Image.fromarray(heightmap.astype(np.uint16), mode="I;16")

        img.save(output_path)

        return output_path, heightmap.shape[1], heightmap.shape[0]

    def _stitch_tiles(
        self,
        tile_data: dict[str, tuple[ASCHeader, np.ndarray]],
        center_e: int,
        center_n: int,
        size_km: int,
    ) -> np.ndarray:
        """
        Stitch multiple tiles together and extract the requested area.

        Args:
            tile_data: Dictionary of tile_name -> (header, data)
            center_e: Center easting in meters
            center_n: Center northing in meters
            size_km: Size of output area in kilometers

        Returns:
            Combined heightmap array
        """
        if not tile_data:
            raise ValueError("No tile data provided")

        # Determine the bounds of all tiles
        min_e = float("inf")
        max_e = float("-inf")
        min_n = float("inf")
        max_n = float("-inf")
        cellsize = None

        for header, _ in tile_data.values():
            if cellsize is None:
                cellsize = header.cellsize
            min_e = min(min_e, header.xllcorner)
            max_e = max(max_e, header.xllcorner + header.ncols * header.cellsize)
            min_n = min(min_n, header.yllcorner)
            max_n = max(max_n, header.yllcorner + header.nrows * header.cellsize)

        # Create a combined array
        combined_width = int((max_e - min_e) / cellsize)
        combined_height = int((max_n - min_n) / cellsize)
        combined = np.full((combined_height, combined_width), -9999.0, dtype=np.float32)

        # Place each tile in the combined array
        for header, data in tile_data.values():
            x_offset = int((header.xllcorner - min_e) / cellsize)
            y_offset = int((max_n - (header.yllcorner + header.nrows * cellsize)) / cellsize)
            combined[y_offset : y_offset + header.nrows, x_offset : x_offset + header.ncols] = data

        # Extract the requested area
        size_m = size_km * 1000
        half_size = size_m / 2

        # Calculate pixel coordinates for the requested area
        left = int((center_e - half_size - min_e) / cellsize)
        right = int((center_e + half_size - min_e) / cellsize)
        bottom = int((max_n - (center_n - half_size)) / cellsize)
        top = int((max_n - (center_n + half_size)) / cellsize)

        # Ensure bounds are within the combined array
        left = max(0, left)
        right = min(combined_width, right)
        top = max(0, top)
        bottom = min(combined_height, bottom)

        extracted = combined[top:bottom, left:right]

        return extracted

    def _normalise_heightmap(self, heightmap: np.ndarray, bit_depth: int) -> np.ndarray:
        """
        Normalise heightmap values to the output bit depth range.

        Args:
            heightmap: Input heightmap array
            bit_depth: Target bit depth (8 or 16)

        Returns:
            normalised array
        """
        # Mask NODATA values
        valid_mask = heightmap != -9999.0
        valid_data = heightmap[valid_mask]

        if len(valid_data) == 0:
            # All NODATA, return zeros
            return np.zeros_like(heightmap)

        # Get min/max of valid data
        min_height = valid_data.min()
        max_height = valid_data.max()

        # Normalise to 0-1
        if max_height > min_height:
            normalised = (heightmap - min_height) / (max_height - min_height)
        else:
            normalised = np.zeros_like(heightmap)

        # Set NODATA to 0
        normalised[~valid_mask] = 0.0

        # Scale to bit depth
        if bit_depth == 8:
            return (normalised * 255).astype(np.uint8)
        else:
            return (normalised * 65535).astype(np.uint16)
