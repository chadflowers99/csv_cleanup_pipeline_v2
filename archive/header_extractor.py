# header_extractor.py

import csv
import chardet

def extract_headers(path):
    # Detect encoding
    with open(path, "rb") as f:
        raw = f.read(4096)  # small chunk is enough
        detected = chardet.detect(raw)
        encoding = detected["encoding"] or "utf-8"

    # Read header using detected encoding
    with open(path, newline="", encoding=encoding, errors="replace") as f:
        reader = csv.reader(f)
        return next(reader)
    

headers = extract_headers("input/loan_approval_dataset.csv")
print(headers)
