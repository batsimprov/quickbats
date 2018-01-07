from datetime import datetime
from quickbats.config import logger
from quickbats.shared import csv_rows
from quickbats.shared import data_file

import_start_date = datetime(2017, 11, 1)

# TODO rewrite this to use Stripe API instead of CSV export, for fully automated process

def parse_stripe_payments():
    """
    Parses the Stripe Payments export file (payments.csv) and generates a
    dictionary with matchable transaction ID for each transaction type.

    We then use this dictionary to look up payment information when we are
    processing transactions.
    """
    payments = {}

    stripe_payments_file = data_file("stripe", "payments_file")
    for row in csv_rows(stripe_payments_file, encoding='latin-1'):
        # skip old records
        created_on = datetime.strptime(row['Created (UTC)'], "%Y-%m-%d %H:%M")
        if created_on < import_start_date:
            continue

        # identify transaction type, then store row under some unique payment
        # identifier which we have access to from vendor data
        if "Bats Improv  - #" in row['Description']:
            # VBO Transaction
            vbo_id = row['Description'][-7:]
            payments["VBO-%s" % vbo_id] = row
        elif ("BATS Improv Inv" in row['Statement Descriptor']) or ("BATS Invoice" in row['Statement Descriptor']):
            # Manually generated invoice, not relevant to this process.
            pass
        elif row['purchased_on (metadata)']:
            # Vouchercart Transaction
            payments[row['id']] = row
        elif row['donation (metadata)']:
            # Donately Transaction
            payments[row['id']] = row
        else:
            logger.warn("unable to categorize this Stripe transaction:")
            logger.warn(str(row))

    return payments
