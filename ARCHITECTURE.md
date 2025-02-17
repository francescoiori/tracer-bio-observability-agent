# Modular Signals and Metrics Observability Agent

## Overview

This project provides a prototype of an observability agent built in Python to track telemetry data from Linux system binaries.
It logs execution details and system resource usage (CPU and memory) into a local SQLite database.
The system is designed for asynchronous processing to ensures performance and adherence to good design patterns to ensure modularity, scalability.

## System Requirements

### Process Tracking and Resource Monitoring
- Track and log execve syscall events with process details. 
- Monitor CPU, memory, and disk usage of executed processes. 
- Link execution records with system resource usage.

### Data Ingestion and Storage
- Efficiently store raw execution logs and system metrics in a database. 
- Support filtering logs by users and executable paths (parent pipeline process). 
- Process and store filtered execution signals and metric data in dedicated tables.

### Asynchronous Data Processing
- Utilize async or multithreading services to ingest execution and metric data efficiently.
- Perform filtering and processing of logs asynchronously to minimize latency.

### Scalability and Extensibility
- Support migration to a remote database with minimal changes.
- Enable message broker integration (e.g., Kafka, RabbitMQ) for scalability.
- Allow distributed processing using worker nodes (e.g., Kubernetes).

### Configuration and Error Handling
- Manage settings via a TOML file (log levels, tracked users, polling intervals, etc.).
- Handle failures gracefully and log errors for debugging. 
- Implement fallback methods for metric collection if primary methods fail.

## Architectural Decisions
Based on the above requirements, the following architectural decisions have been made to implement a  
proof-of-concept prototype agent.

### Tech stack and packages
#### Use of Python:
Python was chosen for its ease of development and ability to quickly implement an end-to-end solution. 
It offers built-in libraries and third-party packages that simplify 
process monitoring, multi-threading, and structured data management.
It also enables rapid prototyping and analysis of collected data. 

- **eBPF & Process Monitoring**: Python has libraries like `bpftrace`, and `psutil` dedicated to process monitoring, which should help monitoring system processes.
- **Concurrency & Parallelism**: Python's `asyncio` and `multiprocessing` modules allow efficient data collection and processing, ensuring real-time observability.
- **Data Handling**: With libraries like `SqlAlchemy` `DuckDB`, `pandas`, and `pyarrow`, Python is highly efficient for structured data storage and querying.

However, as Python can suffer from poor performance, careful consideration has to be given to ensure efficient 
monitoring and data ingestion.

#### Use of `asyncio` for Efficient Data Ingestion
The observability agent must handle high-frequency process events without blocking.
Instead of a multi-threaded design (which suffers from the GIL in Python), `asyncio` provides event-driven, non-blocking execution.

- **Why `asyncio`?** It allows the agent to handle multiple tasks (monitoring processes, collecting CPU usage, writing logs) concurrently, without excessive thread creation.
- **Implementation**: 
  - **Event listeners** (async coroutines) to capture lifecycle events in real-time.
  - **Asynchronous logging** to `sqlite` or parquet files using `aiofiles` and `pyarrow`.

#### `Pydantic` & `SQLAlchemy` for Structured Data Handling
- **`Pydantic`** is used to is used to ensure data integrity by validating the ingested and processed data against known schemas, reducing errors in data handling.
- **`SQLAlchemy ORM`** allows a clean ORM-based interaction with **SQLite** before persisting data in **Parquet**. Using `SQLAlchemy` makes it easier to interact with SQLite in an asynchronous manner while maintaining efficiency.

#### Use of SQLite for Local Data Storage
While Parquet files will be the final data format for querying, an intermediate storage solution like SQLite allows:

- **Lightweight transaction support**: No need for an external database.
- **Indexed Queries**: Faster retrieval of specific events.
- **Persistence**: Logs data before writing to Parquet.

**Alternative Consideration:**
- Using **DuckDB** directly instead of SQLite. However, SQLite provides an **easier integration** with `SQLAlchemy` while still allowing DuckDB to query Parquet efficiently.

#### Grafana for Visualization and Analysis

**Why Grafana?**

- Rich Visualization: Provides dashboards with graphs, tables, and alerts to analyze log and metric data effectively.
- Real-Time Monitoring: Allows real-time tracking of performance metrics. 
- Seamless SQLite Support: Grafana has a built-in SQLite data source (through a plugin), making it easy to connect and query stored metrics. 
- Custom Queries: Supports SQL queries to filter, aggregate, and analyze specific system events.


#### Use of eBPF for Process Signal and Metric Collection
eBPF, via `bpftrace`, is used to collect execve syscall events. This approach was preferred over bcc due to its quicker setup. 
However, during testing `bpftrace` did not work for collecting system metrics, leading to a temporary workaround using `ps`.
While suboptimal, it allows for basic metric collection until a better solution is implemented. 
The Python `Psutil` was also tested but did not integrate well with the asynchronous environment and failed to collect CPU usage.

## Agent Architecture
### Modular Microservice Architecture
Rather than a monolithic agent, the system is designed as multiple independent services or pipelines:

1. **Metrics and Signals Collector (async process monitoring)**
2. **Data Processor (filters, transforms data)**
3. **Query Engine (DuckDB & Parquet storage)**

**Why Microservices?**
- **Scalability**: Additional monitoring agents can be added without modifying the core architecture.
- **Separation of concerns**: Each service handles a **single responsibility**.
- **Fault isolation**: Failure in one component doesn’t crash the entire system.

#### SQLite Tables for Ingestion and Processing
Data ingestion and processing are managed through SQLite tables, ensuring an organized workflow:

  - Executions Table: Stores raw process execution logs. 
  - Metrics Table: Captures raw system metrics. 
  - Processed Executions Table: Stores filtered and enriched execution data, linking processes to their spawning pipelines. 
  - Processed Metrics Table: Contains only the metrics of filtered processes, ensuring relevance.

#### Asynchronous Data Ingestion Services
Two asynchronous services are responsible for streaming data:
  - `BPFTrace` Program Stream: Captures execution events in the `executions` table.
  - `ps` Stream: Collects system usage metrics in the `metrics` table. 
  
These services continuously process lines of shell output and load data into SQLite.

#### Filtering and Processing Workflow
After ingestion, data is filtered and processed through two asynchronous services:

  - Execution records are cleaned and stored in `processed_executions`, ensuring accurate arguments and linking processes to pipelines. 
  - Metrics are filtered by PID and stored in `processed_metrics`, ensuring only relevant data is retained.

#### Query Execution Using DuckDB and Parquet
- **DuckDB** is chosen for **in-memory query execution** with Parquet storage:
  - **Performance**: Optimized for analytical queries on large structured data.
  - **Efficiency**: Runs SQL directly on Parquet without additional indexing.
  - **Ease of use**: Compatible with Pandas for additional analysis.

### **Final Architectural Overview**
```
+---------------------+      +---------------------+      +---------------------+
|  Signal Collector   | ---> |    SQLite Database  | ---> |  Data Processor     |
| (Async Services)   |       | (Centralized Store) | <--- | (ETL pipeline)      |
+---------------------+      +---------------------+      +---------------------+
                                            |
                                            v
                                  +---------------------+
                                  |   Parquet Storage   |
                                  |  & Query Engine     |
                                  |  (DuckDB)           |
                                  +---------------------+

```

- Signal Collectors (async services) monitor and log execution details and system resource usage into a central SQLite database.
- Data Processors filter and extract relevant data from the SQLite database for meaningful insights.
- The processed data is exported to Parquet for long-term storage and queried using DuckDB for analysis.
- This architecture ensures efficient data ingestion, processing, and querying, supporting both real-time and historical analysis.

## Components

### **1. BaseService**
- Handles signal-based graceful shutdown (`SIGINT`).
- Ensures a common structure for services.

### **2. ExecveLoggerService**
- Uses a regex pattern to parse execution logs.
- Stores ongoing processes in a dictionary for tracking.
- Handles `START` and `END` events separately.

### **3. MetricsService**
- Runs an external script (`ps aux`) to capture system metrics.
- Parses and stores each snapshot along with timestamps.
- Uses `ps` instead of `bpftrace` for CPU/memory metrics collection due to compatibility issues. This is a compromise as it may impact performance.

### **4. Execution and Metrics processing**
- Execution signals and metrics are processed by two separate services, that run also asynchronously.
- `execution_processing_service` and `metrics_processing_service`

### **5. DB Repositories**
- Implements database operations using SQLAlchemy.
- One repository for each table:
  - `ExecutionRepository` and `ProcessedExecutionRepository` for the raw and filtered execution signals.
  - `MetricsRepository` and `ProcessedMetricsRepository`for the raw and processed metrics.
- Execution signals and metrics are logged and processed separately.

### **6. Main Application**
- Initializes the database connection.
- Runs `ExecveLoggerService` and `MetricsService` concurrently.
- Handles `asyncio.CancelledError` for graceful shutdown.

## Benefits
- **Modularity** - Each service can run independently or be extended.
- **Scalability** - Supports concurrent execution using `asyncio`.
- **Fault Tolerance** - Implements logging and exception handling for robust error management.
- **Extensibility** - New services or additional parsing rules can be integrated easily.

#### Future Scalability Considerations
- Remote Database Integration: The current SQLite-based architecture can be extended to a remote database with minimal modifications. 
- User Identification: A user table should be introduced to associate executions with specific users. 
- Distributed Processing: The processing workload could be offloaded to worker nodes (e.g., on Kubernetes) to improve scalability. 
- Message Broker for Scalability: Using a message broker like Kafka or RabbitMQ could help manage load and mitigate backpressure, improving system reliability under high data throughput.
- Unit and system testing using pytest and mockups.