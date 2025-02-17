# Tracer Observability Agent

This project is an asynchronous eBPF-based agent that tracks process executions and system resource usage. It logs execution details and system metrics (CPU, memory, disk usage) into a local SQLite database.

## Features

- Tracks process executions (`execve` syscall) using eBPF (`ebpf_execve_service.py`)
- Monitors CPU, memory, and disk usage for tracked processes using `ps` (`metrics_service.py`).
- Raw data is ingested in a local SQLite database.
- 
- Uses SQLAlchemy with async support (`aiosqlite`).
- Basic configuration is managed via a TOML file.

## Project Structure

```
trace-bio-agent/
│── agent.py                 # Main agent script
│── setup.py                 # Setup script for packaging
│── pyproject.toml           # Poetry dependencies and project configuration
│── README.md                # Project documentation
│── ARCHITECTURE.md          # High-level architecture description
│── parquet_files/           # Directory containing Parquet data files
│── query_validation_scripts/
│   ├── execution_analysis.py     # Script for analyzing execution data
│   ├── sql_to_parquet.py         # Converts SQL query results to Parquet files
│   ├── top_n_libraries.py        # Identifies top N libraries used (component 3)
│── lifecycle_scripts/
│   ├── lifecycle.bt              # eBPF script for monitoring process lifecycle
│   ├── metrics_collection.sh     # Shell script for collecting system metrics
│   ├── monitor_lifecycle_events.sh # Script for tracking lifecycle events
│── simulate_pipelines/
│   ├── pipeline_1.sh             # Example pipeline script 1
│   ├── pipeline_2.sh             # Example pipeline script 2
│   ├── run_pipeline.sh           # General pipeline execution script
│   ├── bioinformatics_pipeline.sh # Bioinformatics-specific pipeline
│── tracer_bio_agent/
│   ├── services/
│   │   ├── base_services.py          # Base service class
│   │   ├── ebpf_execve_service.py    # eBPF service tracking execve calls
│   │   ├── execution_processing_service.py # Process execution tracking logic
│   │   ├── metrics_processing_service.py # Processes collected metrics
│   │   ├── metrics_service.py        # Collects system-level metrics (cpu and memory) using ps
│   │   ├── ps_util_metrics_service.py # Uses psutil for additional metrics
│   ├── config.py                # Configuration management
│   ├── crud.py                  # Database repository layer
│   ├── database.py              # Database setup and connection management
│   ├── models.py                # SQLAlchemy models for data storage

```

## Requirements

- Linux (with eBPF support)
- Python 3.12+
- `poetry` for dependency management
- `stress` package used in `pipeline_1` and `pipeline_2.sh`
- `fastqc` , `seqtk`, `bwa`, `samtools`, `htseq-count ` for `bioinformatics_pipeline.sh`

## Installation

```sh
# Install dependencies using Poetry
poetry install
```

## Running the Agent

```sh
sudo /.venv/bin/python agent.py
```

## Configuration (TOML File)

Example configuration file `config.toml`:

```toml
[database]
url = "sqlite+aiosqlite:///./tracer_bio.db"

[monitoring]
interval = 2  # Seconds between metric collection

[processing]
interval = 5  # Seconds between metric processing

[filters]
users = ["francesco-iori", 'root']

[filters.executables]
pipeline_1 = ["stress"]
pipeline_2 = ["stress"]
bioinformatics_pipeline = ["wget", "fastqc", "seqtk", "bwa", "samtools", 'htseq-count']
```
