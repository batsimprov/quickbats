from quickbats.config import CONFIG
import csv
import itertools
import logging
import os

logger = logging.getLogger("quickbats")

def csv_rows(filepath, encoding=None, skip_rows=None):
    logger.debug("at beginning of csv_rows")
    with open(filepath, 'r', encoding=encoding) as f:
        logger.debug("successfully opened %s" % filepath)
        if skip_rows is not None:
            rowiter = itertools.islice(f, skip_rows, None)
        else:
            rowiter = f
        rows = csv.DictReader(rowiter)
        for i, row in enumerate(rows):
            logger.debug("row %s" % i)
            yield row

def data_file(vendor, nick):
    filename = CONFIG[vendor][nick]
    return os.path.join(CONFIG['app']['datadir'], filename)
