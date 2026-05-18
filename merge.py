import pickle
import json
import heapq
from pathlib import Path
from itertools import groupby

BATCH_FOLDER = Path("index_batches")
GLOBAL_INDEX_PATH = Path("global_index.txt")
LEXICON_PATH = Path("lexicon.json")

def merge_indexes():
    index_files = sorted(BATCH_FOLDER.glob("index_part_*.bin"))

    if not index_files:
        print("No partial index files found!")
        return

    loaded_indexes = []
    for file_path in index_files:
        with open(file_path, 'rb') as f:
            loaded_indexes.append(pickle.load(f))

    iterators = [iter(idx.items()) for idx in loaded_indexes]

    print("Iterators prepared. Ready to merge.")

    #feed iterators into heapq.merge
    merged_stream = heapq.merge(*iterators, key=lambda item: item[0])

    #lexicon will hold our byte offsets
    lexicon = {}

    print("Executing linear merge and streaming to global_index.txt")

    with open(GLOBAL_INDEX_PATH, 'wb') as f_out:
        for token, group in groupby(merged_stream, key=lambda item: item[0]):
            combined_postings = []
            for token_str, postings_list in group:
                combined_postings.extend(postings_list)

            lexicon[token] = f_out.tell()
            dataToWrite = f"{token}|{json.dumps(combined_postings)}\n"
            f_out.write(dataToWrite.encode('utf-8'))

if __name__ == "__main__":
    merge_indexes()
