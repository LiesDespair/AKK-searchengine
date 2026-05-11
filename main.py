"""
CORE MODULE: Search Engine Indexer (Milestone 1)
-----------------------------------------------
PURPOSE:
Orchestrates the 'Text Acquisition' and 'Index Creation' phases of the search
engine. It traverses the UCI DEV corpus, performs exact deduplication, and
builds an inverted index with word positions and importance flags.

OPERATIONAL CONSTRAINTS (Developer Track):
- Partial Offloading: To manage memory, the index is cleared and saved to
  disk every 10,000 documents (OFFLOAD_THRESHOLD).
- Deduplication: Uses MD5 content hashing to skip identical pages.
- Persistence: Saves partial indexes as binary .bin files using Pickle.

OUTPUTS:
- partial_indexes/*.bin : Binary inverted index segments.
- url_map.json          : Mapping of DocIDs to original URLs.
"""

from collections import defaultdict
import os
import json
import psutil
from parser_utils import process_content
from indexer import save_index_to_disk
from pathlib import Path
import time
import hashlib

OFFLOAD_THRESHOLD = 10000
BATCH_FOLDER = Path("index_batches")
inverted_index = defaultdict(list)
url_to_id_map = {}
doc_count = 0
batch_num = 0
exact_duplicates_seen = 0
unique_tokens_registry = set() #holds all unique words to help with deduplication later on
seen_content_hashes = set()

#path to temp testing files
data_dir = '../developer/DEV'

def get_total_index_size_kb(directory=BATCH_FOLDER, pattern="index_part_*.bin"):
    total_bytes = sum(f.stat().st_size for f in directory.glob(pattern))
    return total_bytes / 1024

def get_doc_id(url, url_to_id_map):
    if url not in url_to_id_map:
        new_id = len(url_to_id_map)
        url_to_id_map[url] = new_id
        return new_id, True
    return url_to_id_map[url], False

start_time = time.perf_counter()
BATCH_FOLDER.mkdir(parents=True, exist_ok=True)

for root, dirs, files in os.walk(data_dir):
    print('Found directory', root)
    time_before_indexing_folder = time.perf_counter()
    for file in files:
        if file.endswith('.json'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                url = data['url']
                content = data['content']
                content_hash =hashlib.md5(content.encode('utf-8')).hexdigest()

                if content_hash in seen_content_hashes:
                    exact_duplicates_seen += 1
                    continue

                seen_content_hashes.add(content_hash)

                doc_id, is_new_id = get_doc_id(url, url_to_id_map)

                #process the document
                stats = process_content(content)
                unique_tokens_registry.update(stats.keys())

                #importance is stored as 0/1 for future mathematical operations; it is NOT stored as T/F
                for token, (term_freq, positions, importance) in stats.items():
                    inverted_index[token].append((doc_id, term_freq, positions, importance))

                doc_count += 1
                if doc_count % OFFLOAD_THRESHOLD == 0:
                    batch_num += 1
                    file_path = BATCH_FOLDER / f"index_part_{batch_num}.bin"
                    print(f"Offloading partial index {batch_num} at {doc_count} documents...")

                    save_index_to_disk(inverted_index, file_path)
                    inverted_index.clear()
    time_after_indexing_folder = time.perf_counter()
    print(f"Time it took to index {root}: {time_after_indexing_folder - time_before_indexing_folder:.4f} seconds")
                # clear memory when memory usage exceeds 500mb
                # if get_memory_usage_in_megabytes() > 500:
                #     handle_excess_memory_usage()

with open("url_map.json", 'w', encoding='utf-8') as f:
    json.dump(url_to_id_map, f)
print(f"Saved {len(url_to_id_map)} URL map")

if inverted_index:
    batch_num += 1
    file_path = BATCH_FOLDER / f"index_part_{batch_num}.bin"
    save_index_to_disk(inverted_index, file_path)

print(f"\n--- M1 Analytics for {doc_count} Docs ---")
print(f"Total Documents: {doc_count}")
print(f"Total partial index files created: {batch_num}")
print(f"Total number of exact duplicates detected: {exact_duplicates_seen}")
print(f"Unique Tokens: {len(unique_tokens_registry)}")
total_size_of_index_on_disk_kb = get_total_index_size_kb()
print(f"Total Size of Index: {total_size_of_index_on_disk_kb:.2f} KB")
avg_size_per_doc = (total_size_of_index_on_disk_kb / doc_count) if doc_count > 0 else 0
print(f"Average Index Size per Doc: {avg_size_per_doc:.4f} KB")
end_clock=time.perf_counter()
print(f"Total Execution Time: {end_clock - start_time:.4f} seconds")





# FIXME: initially i want to try to load excess files from memory onto drive but this method doesn't work; maybe revisit for fun in the future?
# def get_memory_usage_in_megabytes():
#     process = psutil.Process(os.getpid())
#     return process.memory_info().rss / (1024 * 1024)
#
# def handle_excess_memory_usage():
#     print(f"Memory usage exceeded 500 MB, currently using {get_memory_usage_in_megabytes()} MB--offloading...")
#     global batch_num
#     batch_num += 1
#     file_path = Path("index_batches") / f"index_part_{batch_num}.bin"
#     save_index_to_disk(inverted_index, file_path)
#     inverted_index.clear()  # clear ram for next batch