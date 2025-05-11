import os
import re
import argparse
import pandas as pd
# 
def get_package_name(file_path):
    """
    Extracts the package name from a .go file by scanning for a line starting with 'package'.
    Returns None if no package statement is found.
    """
    package_regex = re.compile(r'^\s*package\s+(\w+)')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Search in the first few lines (typically the package declaration is near the top)
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                match = package_regex.match(line)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def count_non_empty_lines(file_path):
    """
    Counts non-empty lines in a file, excluding comment lines.
    It will skip single-line comments (//) and block comment lines (/* ... */).
    Note: This is a simple heuristic and might not cover all edge cases.
    """
    count = 0
    in_block_comment = False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()

                # Skip blank lines.
                if not stripped_line:
                    continue

                # Handle block comments.
                if in_block_comment:
                    # Look for the end of the block comment.
                    if "*/" in stripped_line:
                        # Remove anything before and including the '*/' then continue processing.
                        # This ensures that if there is code after a block comment termination, we count it.
                        in_block_comment = False
                        # Split the line around the end of block comment.
                        after_comment = stripped_line.split("*/", 1)[1].strip()
                        if not after_comment:
                            continue
                        stripped_line = after_comment
                    else:
                        continue

                # Check if the line starts with a single-line comment.
                if stripped_line.startswith("//"):
                    continue

                # Check if a block comment starts on this line.
                if "/*" in stripped_line:
                    # In some cases, the block comment might be contained on the same line.
                    before_comment = stripped_line.split("/*", 1)[0].strip()
                    after_comment = stripped_line.split("/*", 1)[1]
                    if "*/" in after_comment:
                        # Entire block comment is on the same line.
                        after_comment = after_comment.split("*/", 1)[1].strip()
                        # If there is no code before or after the block comment, skip this line.
                        if not before_comment and not after_comment:
                            continue
                        # Otherwise, use whichever part has code.
                        stripped_line = before_comment if before_comment else after_comment
                    else:
                        # If there's code before the block comment, count it.
                        if before_comment:
                            stripped_line = before_comment
                        else:
                            # Otherwise, consider the rest of the line as part of block comment and set flag.
                            in_block_comment = True
                            continue

                # If we get here, the line contains code (or code mixed with inline comments).
                count += 1

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return count

def count_lines_by_package(root_dir, ignore_packages, skip_folders):
    """
    Walks through directories starting from root_dir and processes .go files.
    Returns a dictionary mapping package names to their total non-empty line counts.
    Packages specified in the ignore_packages list are skipped.
    Directories specified in skip_folders will not be traversed.
    """
    package_line_counts = {}
    
    for subdir, dirs, files in os.walk(root_dir):
        # Remove any directories from the traversal that are in skip_folders.
        dirs[:] = [d for d in dirs if d not in skip_folders]
        
        for file in files:
            if file.endswith('.go'):
                file_path = os.path.join(subdir, file)
                pkg_name = get_package_name(file_path)
                if pkg_name:
                    # Skip the package if it's in the ignore list.
                    if pkg_name in ignore_packages:
                        continue
                    lines = count_non_empty_lines(file_path)
                    package_line_counts[pkg_name] = package_line_counts.get(pkg_name, 0) + lines
    return package_line_counts

def parse_args():
    parser = argparse.ArgumentParser(
        description="Count non-empty lines of code per Go package using a Pandas DataFrame for output."
    )
    parser.add_argument(
        "path",
        type=str,
        help="The root directory path of your Go project."
    )
    parser.add_argument(
        "--ignore-packages", 
        nargs='*', 
        default=[],
        help="List of package names to ignore (e.g. --ignore-packages package1 package2)."
    )
    parser.add_argument(
        "--skip-folders",
        nargs='*',
        default=[],
        help="List of folder names to skip during traversal (e.g. --skip-folders vendor test)."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Display the top X packages sorted by lines of code."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    root_directory = args.path
    ignore_packages = args.ignore_packages
    skip_folders = args.skip_folders
    top_n = args.top

    if not os.path.isdir(root_directory):
        print(f"The provided path '{root_directory}' is not a valid directory.")
        return

    counts = count_lines_by_package(root_directory, ignore_packages, skip_folders)
    
    if counts:
        # Convert the dictionary to a DataFrame.
        df = pd.DataFrame(list(counts.items()), columns=['Package', 'Non-Empty Lines'])
        # Sort the DataFrame by 'Non-Empty Lines' in descending order.
        df.sort_values(by='Non-Empty Lines', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # If --top is provided, limit the output to the top X rows.
        if top_n is not None:
            if top_n < len(df):
                df = df.head(top_n)
            else:
                print(f"Warning: Requested top {top_n} packages, but only {len(df)} packages are available.")
        
        print("Lines of Code per Go Package (sorted highest to lowest):")
        print(df.to_string(index=False))
    else:
        print("No Go packages found in the provided directory (or all packages were ignored/skipped).")

if __name__ == "__main__":
    main()