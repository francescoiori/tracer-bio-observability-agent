# Simulate Pipelines  

The `simulate_pipelines` directory contains shell scripts designed to execute various simulated workloads. These scripts leverage the [`stress`](https://linux.die.net/man/1/stress) tool to generate CPU, memory, and I/O loads, as well as a bioinformatics pipeline that runs a dummy analysis on publicly available files.  

## Folder Structure  

```
simulate_pipelines/ 
│── pipeline_1.sh # Simulates a workload using the stress tool 
│── pipeline_2.sh # Simulates a different workload using the stress tool 
│── run_pipeline.sh # Runs pipeline_1 and pipeline_2 multiple times, then executes the bioinformatics pipeline 
│── bioinformatics_pipeline.sh # Simulates a basic bioinformatics workflow
```

## Pipeline Descriptions  

### 1. `pipeline_1.sh`  and  `pipeline_2.sh` 
This scripts generate a simulated workload using the `stress` tool, applying CPU and memory pressure to evaluate system resource consumption and execution behavior.

### 2. `bioinformatics_pipeline.sh`  
This script simulates a simple bioinformatics pipeline by processing files available online. It does not apply much system stress but instead mimics a data processing workflow.  

### 3. `run_pipeline.sh`  
This script orchestrates the execution of the pipelines:  
1. Runs `pipeline_1.sh` x10.
2. Runs `pipeline_2.sh` x10.
3. Runs `bioinformatics_pipeline.sh` once.  

## Why Use `stress`?  

The `stress` tool is used in `pipeline_1.sh` and `pipeline_2.sh` to simulate real-world workloads by artificially generating CPU, memory, and I/O pressure. This approach allows for:  

- **Performance Evaluation:** Understanding how the system behaves under different workload conditions.  
- **Resource Monitoring:** Capturing system metrics like CPU and memory usage using eBPF and ps monitoring services.  
- **Testing Execution Tracing:** Ensuring the correct functioning of execution tracking scripts within `tracer_bio_agent/services/`.