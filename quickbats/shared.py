from decimal import Decimal
from quickbats.config import CONFIG
import csv
import itertools
import logging
import os

logger = logging.getLogger("quickbats")

def csv_rows(filepath, encoding=None, skip_rows=None, stop_after=None):
    logger.debug("at beginning of csv_rows")
    with open(filepath, 'r', encoding=encoding) as f:
        logger.debug("successfully opened %s" % filepath)
        if skip_rows is not None:
            rowiter = itertools.islice(f, skip_rows, None)
        else:
            rowiter = f
        rows = csv.DictReader(rowiter)
        for i, row in enumerate(rows):
            if stop_after is not None and i >= stop_after:
                break
            logger.debug("row %s" % i)
            yield row


def data_file(vendor, nick):
    filename = CONFIG[vendor][nick]
    return os.path.join(CONFIG['app']['datadir'], filename)


def to_dec(string_with_dollar_sign):
    if "(" and ")" in string_with_dollar_sign:
        # negative value
        return Decimal("-%s" % string_with_dollar_sign.strip("()$"))
    else:
        return Decimal(string_with_dollar_sign.strip("$"))
