import csv
import os
from quickbats.config import CONFIG

def csv_rows(filepath, encoding=None, stop_after=None):
    with open(filepath, 'r', encoding=encoding) as f:
        rows = csv.DictReader(f)
        for i, row in enumerate(rows):
            if stop_after is not None:
                if i >= stop_after:
                    break
            yield row

def data_file(vendor, nick):
    filename = CONFIG[vendor][nick]
    return os.path.join(CONFIG['app']['datadir'], filename)
