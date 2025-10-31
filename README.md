# Yokogawa CQ3000

This repo tests and implements converting Yokogawa CQ3000 plates to OME-Zarr.

## Installation

1. Open a terminal
1. Install [pixi](https://pixi.sh/dev/installation/)
1. Install git if you don't have it already. E.g. using pixi: `pixi global install git`
1. Clone this repository, e.g.: `git clone https://github.com/yourusername/CQ3000_converter.git`
1. Run `pixi run convert-to-ome-zarr --help` to see usage information.

## CLI Usage

A Typer-based CLI is available for converting CQ3000 data:

```bash
# Show help
pixi run convert-to-ome-zarr --help

# Convert acquisition
pixi run convert-to-ome-zarr convert /path/to/input /path/to/output.zarr

# Batch convert multiple acquisitions
pixi run convert-to-ome-zarr batch -i /path/to/data1 -i /path/to/data2 -o /output/dir
```

## References

https://github.com/BioVisionCenter/ome-zarr-converters-tools
https://github.com/fractal-analytics-platform/fractal-uzh-converters