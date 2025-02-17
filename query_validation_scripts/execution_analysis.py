import duckdb
import matplotlib.pyplot as plt


plt.ion()  # Enables interactive mode


# Connect to DuckDB
con = duckdb.connect()

# Load Parquet files
con.execute("INSTALL parquet; LOAD parquet;")

# Query 1: Execution Time Analysis for Libraries
query1 = """
WITH execution_summary AS (
    SELECT 
        m.command AS library,
        AVG(e.duration) AS avg_duration,
        SUM(m.cpu) AS total_cpu_time
    FROM read_parquet('../parquet_files/metrics.parquet') m
    JOIN read_parquet('../parquet_files/executions.parquet') e
    ON m.pid = e.pid
    WHERE e.duration IS NOT NULL
    GROUP BY library
)
SELECT library, avg_duration, total_cpu_time
FROM execution_summary
ORDER BY total_cpu_time DESC
LIMIT 10;
"""
df_execution = con.execute(query1).df()

# Query 2: CPU Usage Trends Over Time (Fix strftime issue)
query2 = """
SELECT 
    strftime(CAST(m.snapshot_time AS TIMESTAMP), '%Y-%m-%d %H:%M') AS time_bucket,
    SUM(m.cpu) AS total_cpu_usage
FROM read_parquet('../parquet_files/metrics.parquet') m
GROUP BY time_bucket
ORDER BY time_bucket;
"""
df_cpu_trends = con.execute(query2).df()

# Plot 1: Execution Time vs CPU Usage for Libraries
plt.figure(figsize=(10, 6))
plt.barh(df_execution['library'], df_execution['total_cpu_time'], color='blue', alpha=0.7)
plt.xlabel("Total CPU Time")
plt.ylabel("Library")
plt.title("Total CPU Time Usage by Library")
plt.gca().invert_yaxis()  # Invert y-axis for better visualization
plt.savefig("execution_time_vs_cpu_usage.png", dpi=300, bbox_inches="tight")

# Plot 2: CPU Usage Trends Over Time
plt.figure(figsize=(12, 6))
plt.plot(df_cpu_trends['time_bucket'], df_cpu_trends['total_cpu_usage'], marker='o', linestyle='-', color='red')
plt.xticks(rotation=45, ha="right")
plt.xlabel("Time (Bucketed by Minute)")
plt.ylabel("Total CPU Usage")
plt.title("CPU Usage Trends Over Time")
plt.grid(True)
plt.savefig("cpu_usage_trends.png", dpi=300, bbox_inches="tight")
