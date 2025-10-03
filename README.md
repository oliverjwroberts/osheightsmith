# OSHeightsmith

A Python CLI tool for creating PNG heightmaps from [Ordnance Survey Terrain 50](https://www.ordnancesurvey.co.uk/products/os-terrain-50) data.

## Prerequisites

This project uses [uv](https://docs.astral.sh/uv/), a Python package and project manager. Please [install it](https://docs.astral.sh/uv/getting-started/installation/) before continuing.

## Installation

```bash
# Clone the repository
git clone https://github.com/oliverjwroberts/osheightsmith
cd osheightsmith

# No need to install dependencies as uv will create an on-demand environment from the pyproject.toml
```

## Setup

1. Download the OS Terrain 50 data, in ASCII Grid format, from the [OS Data Hub](https://osdatahub.os.uk/downloads/open/Terrain50)
2. Place the downloaded `terr50_gagg_gb.zip` file in the `data/` directory

## Usage

You can use https://gridreferencefinder.com/ to find grid references for any UK location.

### Generate a heightmap

```bash
# Generate a heightmap centered on a grid reference
uv run main.py generate ST1876

# Specify a custom size (in km), output path, and bit-depth
uv run main.py generate ST1876 --size 10 --output my_heightmap.png --bit-depth 16
```

### View grid reference information

```bash
# Display information about a grid reference
uv run main.py info ST1876

Grid Reference Information

 Grid reference  ST1876                 
 Easting         318,000 m              
 Northing        176,000 m              
 Precision       1000 m                 
 Area size       10 km × 10 km          
 Required tiles  4                      
 Tile names      st17, st18, st27, st28
```

## Options

- `--size`, `-s`: Size of the area in kilometers (default: 10)
- `--zip-path`, `-z`: Path to OS Terrain 50 zip file (default: `data/terr50_gagg_gb.zip`)
- `--output`, `-o`: Output PNG filename (default: auto-generated in `heightmaps/`)
- `--bit-depth`, `-b`: Bit depth for PNG, 8 or 16 (default: 16)


