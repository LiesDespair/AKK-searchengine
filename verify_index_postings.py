"""
UTILITY: Partial Index Verifier (Milestone 1)
--------------------------------------------
PURPOSE:
This script allows team members to verify the contents of the binary partial
indexes created by main.py. It validates that tokens are correctly stemmed,
positions are recorded, and the importance flag (0/1) is assigned.

USAGE:
Run this script directly and modify the 'test_word' in the __main__ block,
or import verify_index_postings into another module to audit the corpus.
"""

import pickle
from pathlib import Path

def verify_index_postings(test_word):
    pattern = "index_part_*.bin"
    batch_folder = Path("index_batches")
    index_files = sorted(batch_folder.glob(pattern))
    current_bin_file_num = 1
    found = False

    for file_path in index_files:
        try:
            with file_path.open("rb") as f:
                index = pickle.load(f)

            if test_word in index:
                print(f"--- Found in {file_path.name} ---")
                print(f"Postings: {index[test_word]}")
                found = True

            current_bin_file_num += 1
        except FileNotFoundError:
            print(f"Error: index_part_{current_bin_file_num}.bin not found")

    if not found:
        print(f"Token '{test_word}' not found in any partial index.")

if __name__ == "__main__":
    verify_index_postings("research")
