from datetime import datetime
from decimal import Decimal
from quickbats.config import one
from quickbats.line_items import stripe_fee_line_item
from quickbats.line_items import transaction_line_item
from quickbats.qbo import CreateReceipt
from quickbats.shared import csv_rows
from quickbats.shared import data_file
import logging

logger = logging.getLogger("quickbats")


def vouchercart_customer_attrs(row):
    display_name = "%s (%s)" % (row['CustomerName'], row['CustomerEmail'])
    customer_attrs = {
            "PrimaryEmailAddr" : row['CustomerEmail'],
            "PrimaryPhone" : row['CustomerPhone']
            }
    return display_name, customer_attrs


def vouchercart_customer(qbo, row):
    display_name, customer_attrs = vouchercart_customer_attrs(row)
    return qbo.find_or_create_customer(display_name, customer_attrs)


def vouchercart_doc_number(row):
    return "VOUCHER-%s" % row['OrderID'][0:12]


def parse_vouchercart_transactions(qbo, payments):
    vouchercart_transactions_file = data_file("vouchercart", "transactions_file")
    stripe_fees_item = qbo.get_item_by_name("Stripe Fees (Vouchers)")
    credit_card_receivables_account = qbo.get_account_by_name("Stripe Receivables")
    qbo_class = qbo.get_class_by_name("2 School")

    active_doc_number = None
    active_order = []

    def process_order():
        doc_number = active_doc_number
        first_row = active_order[0]

        logger.debug("processing order %s" % doc_number)

        customer = vouchercart_customer(qbo, first_row)
        order_date = datetime.strptime(first_row['OrderDate'], "%m/%d/%Y %H:%M")
        total = sum(Decimal(row["VoucherPrice"]) for row in active_order)

        with CreateReceipt(qbo, test_mode=True) as receipt:
            receipt.CustomerRef = customer.to_ref()
            receipt.DocNumber = doc_number
            receipt.TxnDate = order_date.strftime("%Y-%m-%d")

            receipt.PrivateNote = "Imported via QBO API from Vouchercart export."

            for row in active_order:
                assert vouchercart_doc_number(row) == doc_number
                voucher_line_item = transaction_line_item(
                        Decimal(row['VoucherPrice']),
                        row['VoucherTitle'],
                        one,
                        qbo.get_item_by_name(row['VoucherTitle']),
                        order_date,
                        qbo_class=qbo_class)
                receipt.Line.append(voucher_line_item)

            receipt.Line.append(stripe_fee_line_item(payments, total, first_row['PaymentReference'], stripe_fees_item, order_date, qbo_class=qbo_class))

            receipt.DepositToAccountRef = credit_card_receivables_account.to_ref()

    # an order may have multiple rows
    # aggregate the rows for each order, then process all rows at once
    for row in csv_rows(vouchercart_transactions_file):
        doc_number = vouchercart_doc_number(row)

        if "Imported-" in row['OrderID']:
            logger.debug("skipping imported voucher")
            continue

        logger.debug("doc_number is %s" % doc_number)

        if qbo.already_processed(doc_number):
            continue
        elif row['PaymentReference'] not in payments:
            logger.debug("fee information not available yet, skipping %s" % doc_number)
            continue

        if doc_number == active_doc_number:
            logger.debug("appending additional row to current order")
            active_order.append(row)
        else:
            if active_doc_number is not None:
                process_order()
            active_doc_number = doc_number
            active_order = [row]

    # process the last order
    if active_doc_number is not None:
        process_order()
