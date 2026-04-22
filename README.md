# Yokogawa CQ3000

This repo tests and implements converting Yokogawa CQ3000 plates to OME-Zarr.

It uses the `fractal-uzh-converters` package to perform the conversion, and provides a CLI interface to convert single acquisitions or batch convert multiple acquisitions.

## CLI Usage

### Installation-free usage

Note: `uv` is required to run the commands without installing the package itself. See the [Installation](#installation) section for instructions on how to install `uv`.

```bash
# Show help
uvx --from git+https://github.com/m-albert/CQ3000_converter cq3000-to-ome-zarr --help

# Convert a single acquisition
uvx --from git+https://github.com/m-albert/CQ3000_converter cq3000-to-ome-zarr convert /path/to/input /path/to/output.zarr

# Batch convert multiple acquisitions
uvx --from git+https://github.com/m-albert/CQ3000_converter cq3000-to-ome-zarr batch -i /path/to/data1 -i /path/to/data2 -o /output/dir
```

### Local usage

```bash
# Show help
uv run cq3000-to-ome-zarr --help

# Convert a single acquisition
uv run cq3000-to-ome-zarr convert /path/to/input /path/to/output.zarr

# Batch convert multiple acquisitions
uv run cq3000-to-ome-zarr batch -i /path/to/data1 -i /path/to/data2 -o /output/dir
```

## Installation

### Installing uv

`uv` is a Python package manager and environment manager that simplifies the process of installing and managing Python packages and their dependencies.

Installation instructions are [here](https://docs.astral.sh/uv/getting-started/installation/). On most systems, you can install `uv` using the following command in your terminal:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh   
```

### Package installation

Clone the repository and run the commands from the local directory:

1. Open a terminal and navigate to the directory where you want to clone the repository
1. Install [git](https://git-scm.com/downloads) if not already available
1. Clone this repository: `git clone https://github.com/m-albert/CQ3000_converter.git`
1. Change into the repository directory: `cd CQ3000_converter`  
1. Run `uv sync` to create the python environment and install dependencies

## References

https://github.com/fractal-analytics-platform/fractal-uzh-converters