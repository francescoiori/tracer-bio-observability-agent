import sqlite3
import pandas as pd
import os
import argparse


def convert_sqlite_to_parquet(sqlite_db_path: str, output_dir: str):
    """
    Converts an SQLite database into Parquet files, saving each table as a separate Parquet file.

    Args:
        sqlite_db_path (str): Path to the SQLite database file.
        output_dir (str): Directory where Parquet files will be stored.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Connect to the SQLite database
    conn = sqlite3.connect(sqlite_db_path)

    # Fetch all table names
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql(query, conn)

    if tables.empty:
        print("No tables found in the database.")
        return

    print(f"Found {len(tables)} tables: {tables['name'].tolist()}")

    # Convert each table to a Parquet file
    for table_name in tables["name"]:
        df = pd.read_sql(f"SELECT * FROM {table_name};", conn)
        output_file = os.path.join(output_dir, f"{table_name}.parquet")

        df.to_parquet(output_file, engine="pyarrow", index=False)
        print(f"✅ Converted table '{table_name}' to '{output_file}'")

    # Close the database connection
    conn.close()
    print("Conversion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert SQLite DB to Parquet files")
    parser.add_argument("sqlite_db_path", type=str, help="Path to the SQLite database file")
    parser.add_argument("output_dir", type=str, help="Directory to save Parquet files")
    args = parser.parse_args()

    convert_sqlite_to_parquet(args.sqlite_db_path, args.output_dir)
