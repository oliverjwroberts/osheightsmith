"""CLI interface for OSHeightsmith."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .heightmap import HeightmapGenerator

app = typer.Typer(
    name="osheightsmith",
    help="A Python CLI tool for creating PNG height maps from Ordnance Survey Terrain 50 data.",
    add_completion=False,
)

console = Console()


@app.command()
def generate(
    grid_ref: str = typer.Argument(
        ...,
        help="UK grid reference (e.g., ST1876 for Cardiff)",
    ),
    size: int = typer.Option(
        10,
        "--size",
        "-s",
        help="Size of the area in kilometers",
        min=1,
    ),
    zip_path: str = typer.Option(
        "data/terr50_gagg_gb.zip",
        "--zip-path",
        "-z",
        help="Path to OS Terrain 50 zip file",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output PNG filename (default: auto-generated)",
    ),
    bit_depth: int = typer.Option(
        16,
        "--bit-depth",
        "-b",
        help="Bit depth for PNG (8 or 16)",
    ),
    fill_missing: bool = typer.Option(
        True,
        "--fill-missing/--no-fill-missing",
        help="Fill missing tiles with zero-height placeholders",
    ),
) -> None:
    """
    Generate a square PNG heightmap from OS Terrain 50 data.

    The heightmap will be centered on the provided grid reference and cover
    a square area of the specified size.
    """
    try:
        # Validate inputs
        if bit_depth not in [8, 16]:
            console.print("[red]Error: bit-depth must be 8 or 16[/red]")
            raise typer.Exit(1)

        # Create generator
        console.print(f"Loading terrain data from [cyan]{zip_path}[/cyan]...")
        generator = HeightmapGenerator(zip_path)

        # Generate heightmap
        console.print(
            f"Generating heightmap for [cyan]{grid_ref}[/cyan] ([cyan]{size}km[/cyan] area)..."
        )
        output_path, width, height = generator.generate_heightmap(
            grid_ref=grid_ref,
            size_km=size,
            output_path=output,
            bit_depth=bit_depth,
            fill_missing=fill_missing,
        )

        # Display results
        console.print("\n[green]✓[/green] Heightmap generated successfully!\n")

        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Output file", output_path)
        table.add_row("Dimensions", f"{width} × {height} pixels")
        table.add_row("Bit depth", f"{bit_depth}-bit")
        table.add_row("Coverage area", f"{size} km²")
        table.add_row("Grid reference", grid_ref.upper())

        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info(
    grid_ref: str = typer.Argument(
        ...,
        help="UK grid reference to analyse",
    ),
    size: int = typer.Option(
        10,
        "--size",
        "-s",
        help="Size of the area in kilometers",
        min=1,
    ),
) -> None:
    """
    Display information about a grid reference without generating a heightmap.
    """
    try:
        from .grid_reference import get_tiles_for_area, parse_grid_reference

        # Parse grid reference
        easting, northing, precision = parse_grid_reference(grid_ref)

        # Get required tiles
        tiles = get_tiles_for_area(easting, northing, size)

        # Display information
        console.print("\n[cyan]Grid Reference Information[/cyan]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Grid reference", grid_ref.upper())
        table.add_row("Easting", f"{easting:,} m")
        table.add_row("Northing", f"{northing:,} m")
        table.add_row("Precision", f"{precision} m")
        table.add_row("Area size", f"{size} km × {size} km")
        table.add_row("Required tiles", f"{len(tiles)}")
        table.add_row("Tile names", ", ".join(tiles))

        console.print(table)
        console.print()

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app()
