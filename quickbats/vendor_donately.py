from datetime import datetime
from decimal import Decimal
from quickbats.config import CONFIG
from quickbats.config import one
from quickbats.line_items import stripe_fee_line_item
from quickbats.line_items import transaction_line_item
from quickbats.line_items import vendor_rate_line_item
from quickbats.qbo import CreateReceipt
from quickbats.shared import csv_rows
from quickbats.shared import data_file
import logging

DONATION_ITEM_NAME = "Online Donation"

logger = logging.getLogger("quickbats")


def donately_customer_attrs(row):
    display_name = "%s %s (%s)" % (row['First Name'], row['Last Name'], row['Email'])
    customer_attrs = {
            "PrimaryEmailAddr": row['Email'],
            "PrimaryPhone": row['Phone Number']
            }
    return display_name, customer_attrs


def donately_customer(qbo, row):
    display_name, customer_attrs = donately_customer_attrs(row)
    return qbo.find_or_create_customer(display_name, customer_attrs)


def donately_doc_number(row):
    return row['Donation Id'].split()[0]


def parse_donately_transactions(qbo, payments):
    donately_transactions_file = data_file("donately", "transactions_file")
    donation_item = qbo.get_item_by_name(DONATION_ITEM_NAME)
    donately_fees_item = qbo.get_item_by_name("Donately Fees")
    stripe_fees_item = qbo.get_item_by_name("Stripe Fees (Donations)")
    credit_card_receivables_account = qbo.get_account_by_name("Stripe Receivables")
    qbo_class = qbo.get_class_by_name("5 Fundraising")

    for row in csv_rows(donately_transactions_file):
        doc_number = donately_doc_number(row)
        transaction_id = row['Transaction Id']
        donation_type = row['Donation Type']
        order_date = datetime.strptime(row['Custom Donation Date'], "%Y-%m-%d %H:%M:%S %Z")
        total = Decimal(row['Amount in Dollars'])

        logger.debug("doc number is %s" % doc_number)
        logger.debug("donation type is %s" % donation_type)

        if qbo.already_processed(doc_number):
            continue
        elif donation_type == 'cc' and transaction_id not in payments:
            msg = "fee information not available yet, skipping %s" % doc_number
            logger.info(msg)
            continue

        customer = donately_customer(qbo, row)

        with CreateReceipt(qbo) as receipt:
            receipt.CustomerRef = customer.to_ref()
            receipt.DocNumber = doc_number
            receipt.TxnDate = order_date.strftime("%Y-%m-%d")

            notes = ["Imported via QBO API from Donately export."]
            if row['Comment']:
                notes.append(row['Comment'])
            note = u"\n".join(notes)
            receipt.PrivateNote = note

            line1 = transaction_line_item(total, "Donation", one, donation_item, order_date, qbo_class=qbo_class)

            if donation_type == 'cc':
                line2 = vendor_rate_line_item(total, CONFIG['donately']['rate'], donately_fees_item, order_date, qbo_class=qbo_class)
                line3 = stripe_fee_line_item(payments, total, row['Transaction Id'], stripe_fees_item, order_date, abs(line2.Amount), qbo_class=qbo_class)

                receipt.Line = [line1, line2, line3]
                receipt.DepositToAccountRef = credit_card_receivables_account.to_ref()
            else:
                receipt.Line = [line1]
