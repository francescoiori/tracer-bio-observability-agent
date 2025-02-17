import duckdb


def print_query_libraries(con, query, label):
    # Execute the query
    top_processes = con.execute(query).fetchall()

    # Print results in a formatted table
    print(f"\nTop 10 CPU-Consuming {label}\n" + "=" * 40)
    print(f"{'Process':<50} {'CPU Hours':>12}")
    print("-" * 65)

    for process, cpu_seconds in top_processes:
        cpu_hours = (cpu_seconds / 3600) * 5  # Convert CPU seconds to adjusted CPU hours
        print(f"{process:<50} {cpu_hours:>12.2f}")

    print("-" * 65)


def main():
    # Connect to DuckDB and load Parquet files
    con = duckdb.connect()
    con.execute("INSTALL parquet; LOAD parquet;")  # Ensure Parquet support

    # Define the queries
    query_libraries = """
    WITH library_usage AS (
        SELECT 
            command AS library,
            SUM(cpu) AS total_cpu_time
        FROM read_parquet('../parquet_files/metrics.parquet')
        WHERE command LIKE '%.so%' -- Shared object libraries
           OR command LIKE '/lib/%' 
           OR command LIKE '/usr/lib/%' 
           OR command LIKE '/usr/local/lib/%'  -- Include more library paths
        GROUP BY library
    )
    SELECT library, total_cpu_time
    FROM library_usage
    ORDER BY total_cpu_time DESC
    LIMIT 10;
    """

    query_processes = """
    SELECT 
        command AS process,
        SUM(cpu) AS total_cpu_time
    FROM read_parquet('../parquet_files/metrics.parquet')
    WHERE cpu > 0.01  -- Filter for noticeable CPU usage
    GROUP BY process
    ORDER BY total_cpu_time DESC
    LIMIT 10;
    """

    print_query_libraries(con, query_libraries, label='Libraries')
    print_query_libraries(con, query_processes, label='Processes')


if __name__ == '__main__':
    main()
