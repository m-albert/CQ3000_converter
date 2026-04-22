# Yokogawa CQ3000

This repo tests and implements converting Yokogawa CQ3000 plates to OME-Zarr.

## Installation

### Installing uv

`uv` is a Python package manager and environment manager that simplifies the process of installing and managing Python packages and their dependencies.

Installation instructions: https://docs.astral.sh/uv/getting-started/installation/.


### Package installation

Include the following option in the commands below to run the scripts without installing the package:

`--from git+https://github.com/m-albert/CQ3000_converter.git`

Or, clone the repository and run the commands from the local directory:

1. Open a terminal
1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
1. Install [git](https://git-scm.com/downloads) if not already available
1. Clone this repository: `git clone https://github.com/yourusername/CQ3000_converter.git`
1. Run `uv sync` to create the environment and install dependencies

## CLI Usage

```bash
# Show help
uv run convert-to-ome-zarr --help

# Convert a single acquisition
uv run convert-to-ome-zarr convert /path/to/input /path/to/output.zarr

# Batch convert multiple acquisitions
uv run convert-to-ome-zarr batch -i /path/to/data1 -i /path/to/data2 -o /output/dir
```

## References

https://github.com/fractal-analytics-platform/fractal-uzh-converters