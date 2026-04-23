#!/usr/bin/env python3
"""
CQ3000 Converter CLI - Convert Yokogawa CQ3000 data to OME-Zarr format.
"""
from pathlib import Path
from typing import Optional, List
import warnings

import joblib
import typer
from typing_extensions import Annotated
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, MofNCompleteColumn, TimeElapsedColumn

from ome_zarr_converters_tools import AdvancedComputeOptions
from fractal_uzh_converters.cq3k.convert_cq3k_compute_task import (
    convert_cq3k_compute_task,
)
from fractal_uzh_converters.cq3k.convert_cq3k_init_task import (
    convert_cq3k_init_task,
)
from fractal_uzh_converters.olympus_scanr.convert_scanr_init_task import (
    AcquisitionInputModel,
)

app = typer.Typer(
    name="cq3k-converter",
    help="Convert Yokogawa CQ3000 microscopy data to OME-Zarr format",
    add_completion=False,
)
console = Console()


def _suppress_known_runtime_warnings() -> None:
    """Silence noisy third-party warnings that are not actionable for this CLI."""
    warnings.filterwarnings(
        "ignore",
        message=r"Writing zarr v2 data will no longer be the default.*",
        category=UserWarning,
        module=r"anndata\._io\.zarr",
    )


def _compute_task_worker(**kwargs):
    """Run convert_cq3k_compute_task with warning suppression (safe in worker processes)."""
    _suppress_known_runtime_warnings()
    return convert_cq3k_compute_task(**kwargs)


@app.command()
def convert(
    input_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the CQ3000 acquisition data directory",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    output_zarr: Annotated[
        Path,
        typer.Argument(
            help="Path to output OME-Zarr directory",
        ),
    ],
    acquisition_id: Annotated[
        int,
        typer.Option(
            "--acquisition-id",
            "-a",
            help="Acquisition ID for the dataset",
        ),
    ] = 0,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite/--no-overwrite",
            "-o/-O",
            help="Overwrite existing output if it exists",
        ),
    ] = False,
    show_progress: Annotated[
        bool,
        typer.Option(
            "--progress/--no-progress",
            "-p/-P",
            help="Show progress bar during conversion",
        ),
    ] = True,
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel/--no-parallel",
            help="Process tasks in parallel using joblib",
        ),
    ] = True,
    n_jobs: Annotated[
        int,
        typer.Option(
            "--n-jobs",
            help="Number of parallel jobs (-1 = all CPUs)",
        ),
    ] = -1,
) -> None:
    """
    Convert a CQ3000 acquisition to OME-Zarr format.

    This command performs both initialization and compute tasks to convert
    Yokogawa CQ3000 microscopy data into the OME-Zarr format.

    Example:
        cq3k-converter convert /path/to/cq3k/data /path/to/output.zarr
    """
    console.print(f"[bold blue]CQ3000 to OME-Zarr Converter[/bold blue]")
    console.print(f"Input:  {input_path}")
    console.print(f"Output: {output_zarr}")
    console.print()
    _suppress_known_runtime_warnings()

    try:
        # Check if output exists
        if output_zarr.exists() and not overwrite:
            console.print(
                f"[bold red]Error:[/bold red] Output directory '{output_zarr}' already exists. "
                "Use --overwrite to replace it.",
            )
            raise typer.Exit(code=1)

        # Step 1: Initialize conversion
        console.print("[bold green]Step 1:[/bold green] Initializing conversion...")

        p_list = convert_cq3k_init_task(
            zarr_dir=str(output_zarr),
            acquisitions=[
                AcquisitionInputModel(
                    path=str(input_path),
                    acquisition_id=acquisition_id,
                ),
            ],
            overwrite=overwrite,
            advanced_options=AdvancedComputeOptions(invert_y=True),
        )

        num_tasks = len(p_list["parallelization_list"])
        console.print(f"[green]✓[/green] Initialization complete. {num_tasks} tasks to process.")
        console.print()

        # Step 2: Run compute tasks
        console.print("[bold green]Step 2:[/bold green] Converting data...")

        parallelization_list = p_list["parallelization_list"]

        if parallel:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            ) as progress:
                task = progress.add_task(
                    "Converting (parallel)...",
                    total=num_tasks,
                )
                for _ in joblib.Parallel(
                    n_jobs=n_jobs, return_as="generator_unordered", verbose=0
                )(
                    joblib.delayed(_compute_task_worker)(**p)
                    for p in parallelization_list
                ):
                    progress.advance(task)
        elif show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Processing {num_tasks} tasks...",
                    total=num_tasks,
                )

                for i, p in enumerate(parallelization_list):
                    progress.update(task, description=f"Processing task {i+1}/{num_tasks}...")
                    results = _compute_task_worker(**p)

                    if "image_list_updates" not in results:
                        console.print(
                            f"[bold yellow]Warning:[/bold yellow] Task {i+1} missing image_list_updates",
                        )

                    progress.advance(task)
        else:
            for i, p in enumerate(parallelization_list):
                console.print(f"Processing task {i+1}/{num_tasks}...")
                results = _compute_task_worker(**p)

                if "image_list_updates" not in results:
                    console.print(
                        f"[bold yellow]Warning:[/bold yellow] Task {i+1} missing image_list_updates",
                    )

        console.print()
        console.print("[bold green]✓ Conversion completed successfully![/bold green]")
        console.print(f"Output saved to: {output_zarr}")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    config_file: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to batch configuration file (JSON or text with paths)",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    input_paths: Annotated[
        Optional[List[Path]],
        typer.Option(
            "--input",
            "-i",
            help="Input CQ3000 data paths (can be specified multiple times)",
        ),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Base output directory for all conversions",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite/--no-overwrite",
            help="Overwrite existing outputs",
        ),
    ] = False,
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel/--no-parallel",
            help="Process tasks in parallel using joblib",
        ),
    ] = True,
    n_jobs: Annotated[
        int,
        typer.Option(
            "--n-jobs",
            help="Number of parallel jobs (-1 = all CPUs)",
        ),
    ] = -1,
) -> None:
    """
    Batch convert multiple CQ3000 acquisitions.

    You can either provide a config file or use --input options multiple times.

    Example:
        cq3k-converter batch -i /path/to/data1 -i /path/to/data2 -o /path/to/output
    """
    if not input_paths and not config_file:
        console.print(
            "[bold red]Error:[/bold red] Either provide --input paths or a config file",
        )
        raise typer.Exit(code=1)

    _suppress_known_runtime_warnings()

    if not output_dir:
        console.print(
            "[bold red]Error:[/bold red] --output-dir is required for batch processing",
        )
        raise typer.Exit(code=1)

    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)

    paths_to_process = input_paths or []

    if config_file:
        # Read paths from config file (simple text format, one path per line)
        console.print(f"Reading config from: {config_file}")
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    paths_to_process.append(Path(line))

    console.print(f"\n[bold blue]Batch Processing {len(paths_to_process)} acquisitions[/bold blue]\n")

    success_count = 0
    failed = []

    for idx, input_path in enumerate(paths_to_process, 1):
        console.print(f"\n[bold]Processing {idx}/{len(paths_to_process)}:[/bold] {input_path.name}")

        output_zarr = output_dir / f"{input_path.name}_ome_zarr"

        try:
            # Initialize
            p_list = convert_cq3k_init_task(
                zarr_dir=str(output_zarr),
                acquisitions=[
                    AcquisitionInputModel(
                        path=str(input_path),
                        acquisition_id=idx - 1,
                    ),
                ],
                overwrite=overwrite,
                advanced_options=AdvancedComputeOptions(invert_y=True),
            )

            # Convert
            n_tasks = len(p_list["parallelization_list"])
            if parallel:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    MofNCompleteColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    transient=False,
                ) as progress:
                    task = progress.add_task(
                        "Converting (parallel)...",
                        total=n_tasks,
                    )
                    for _ in joblib.Parallel(
                        n_jobs=n_jobs, return_as="generator_unordered", verbose=0
                    )(
                        joblib.delayed(_compute_task_worker)(**p)
                        for p in p_list["parallelization_list"]
                    ):
                        progress.advance(task)
            else:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Converting...", total=len(p_list["parallelization_list"]))

                    for p in p_list["parallelization_list"]:
                        _compute_task_worker(**p)
                        progress.advance(task)

            console.print(f"[green]✓ Completed: {input_path.name}[/green]")
            success_count += 1

        except Exception as e:
            console.print(f"[red]✗ Failed: {input_path.name} - {str(e)}[/red]")
            failed.append((input_path.name, str(e)))

    # Summary
    console.print("\n" + "=" * 50)
    console.print(f"[bold]Batch Processing Summary[/bold]")
    console.print(f"Total: {len(paths_to_process)}")
    console.print(f"[green]Success: {success_count}[/green]")
    console.print(f"[red]Failed: {len(failed)}[/red]")

    if failed:
        console.print("\n[bold red]Failed conversions:[/bold red]")
        for name, error in failed:
            console.print(f"  • {name}: {error}")


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold]CQ3000 Converter CLI[/bold]")
    console.print("Version: 0.1.0")
    console.print("Author: Marvin Albert")


if __name__ == "__main__":
    app()
