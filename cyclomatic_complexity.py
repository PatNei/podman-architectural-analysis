#!/usr/bin/env python3
"""
A Python script to read a text file that contains cyclomatic complexity information
in the format:
    <complexity> <package> <function> <file:line:column>
It groups the data by package and computes the following per package:
   - Total Complexity: sum of complexities from all functions in the package.
   - Average Complexity: average cyclomatic complexity (rounded to two decimals).
   - Function Count: the number of functions.
It accepts a sorting flag to determine which column/header to sort by,
and a --reverse flag to invert the sort order.
Allowed sort headers are:
  - Package (alphabetical order by default)
  - Total_Complexity (descending order by default)
  - Average_Complexity (descending order by default)
  - Function_Count (descending order by default)
If no sort flag is provided, it defaults to sorting by 'Average_Complexity'.
"""

import sys
import argparse
import pandas as pd

def parse_line(line):
    """
    Parses a single line from the file.
    Expected format:
        <complexity> <package> <function> <file:line:column>
    Returns a dictionary with keys: Complexity and Package.
    Function and Location are ignored.
    """
    line = line.strip()
    if not line:
        return None
    parts = line.split()
    if len(parts) < 4:
        print(f"Skipping malformed line: {line}")
        return None
    try:
        complexity = int(parts[0])
    except ValueError:
        print(f"Invalid complexity '{parts[0]}' in line: {line}")
        return None
    package = parts[1]
    return {"Complexity": complexity, "Package": package}

def load_data(file_path):
    """
    Reads the file at file_path, parses each valid line,
    and returns a list of dictionaries containing complexity and package.
    """
    records = []
    try:
        with open(file_path, "r") as file:
            for line in file:
                record = parse_line(line)
                if record:
                    records.append(record)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    return records

def main():
    # Create the argument parser.
    parser = argparse.ArgumentParser(
        description="Process cyclomatic complexity info and sort by column header."
    )
    
    # File path argument.
    parser.add_argument("file_path", help="Path to the input text file")
    
    # Optional sorting flag: now includes "Package" along with the other numeric metrics.
    parser.add_argument(
        "--sort",
        dest="sort_header",
        default="Average_Complexity",
        choices=["Package", "Total_Complexity", "Average_Complexity", "Function_Count"],
        help="Header to sort the results by (default: Average_Complexity). For Package, sorting is alphabetical."
    )
    
    # Optional reverse flag to invert the sorting order.
    parser.add_argument(
        "--reverse",
        dest="reverse",
        action="store_true",
        help="Invert the default sorting order."
    )
    
    # Parse the arguments.
    args = parser.parse_args()
    
    file_path = args.file_path
    sort_header = args.sort_header
    reverse_flag = args.reverse
    
    # Load and process data.
    records = load_data(file_path)
    if not records:
        print("No valid data was found in the file.")
        sys.exit(0)
    
    # Create a DataFrame from the records.
    df = pd.DataFrame(records)
    
    # Group by package to calculate total complexity, average complexity, and function count.
    df_aggregated = df.groupby("Package", as_index=False).agg(
        Total_Complexity=("Complexity", "sum"),
        Average_Complexity=("Complexity", "mean"),
        Function_Count=("Complexity", "count")
    )
    
    # Round the Average_Complexity for readability.
    df_aggregated["Average_Complexity"] = df_aggregated["Average_Complexity"].round(2)
    
    # Determine the default sorting order:
    # - For Package: ascending order by default.
    # - For numeric headers: descending order by default.
    if sort_header == "Package":
        default_ascending = True
    else:
        default_ascending = False
    
    # Apply reverse flag if provided.
    ascending = not default_ascending if reverse_flag else default_ascending
    
    # Sort the DataFrame based on the provided header and order.
    df_aggregated = df_aggregated.sort_values(sort_header, ascending=ascending).reset_index(drop=True)
    
    # Output the results as a nicely formatted DataFrame.
    print(df_aggregated.to_string(index=False))
    
if __name__ == "__main__":
    main()