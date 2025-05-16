#!/usr/bin/env python3
"""Simple script to test NPK extraction directly."""

# todo: script should be removed once NPK module is migrated.

import os
import sys
import traceback

# Import the NPK module
from core.npk import NPKFile

def main():
    """Main function to test NPK file extraction."""
    # Path to the NPK file
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_npk_file>")
        return 1

    npk_path = os.path.expanduser(sys.argv[1])

    if not os.path.exists(npk_path):
        print(f"Error: File does not exist: {npk_path}")
        return 1

    print(f"Opening NPK file: {npk_path}")

    try:
        # Create output directory
        output_dir = os.path.expanduser("./npk_test_output")
        os.makedirs(output_dir, exist_ok=True)

        # Open NPK file
        npk = NPKFile(npk_path)
        print("File opened successfully")
        print(f"File count: {npk.file_count}")

        # Extract first 5 files
        print(f"Extracting first 5 files to {output_dir}")
        extracted = []

        for i in range(min(5, npk.file_count)):
            try:
                entry = npk.get_entry(i)
                out_file = os.path.join(output_dir, entry.filename)

                print(f"Extracting file {i}: {len(entry.data)} bytes, extension: {entry.extension}")
                entry.save_to_file(out_file)
                extracted.append(out_file)
                print(f"Saved to: {out_file}")
            except Exception as e:
                print(f"Error extracting file {i}: {e}")
                traceback.print_exc()

        print(f"Extracted {len(extracted)} files")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
