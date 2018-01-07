from datetime import datetime
from decimal import Decimal
from quickbats.config import CONFIG
from quickbats.line_items import stripe_fee_line_item
from quickbats.line_items import transaction_line_item
from quickbats.line_items import vendor_unit_fee_line_item
from quickbats.qbo import CreateReceipt
from quickbats.shared import csv_rows
from quickbats.shared import data_file
import logging

logger = logging.getLogger("quickbats")


def to_dec(string_with_dollar_sign):
    return Decimal(string_with_dollar_sign.strip("$"))


def vbo_customer(qbo, row):
    display_name = "%s %s (%s)" % (row['First Name'], row['Last Name'], row['Email Address'])
    if display_name == "  ()":
        display_name = "Theatre Patron"
        customer_attrs = {}
    else:
        customer_attrs = {
                "PrimaryEmailAddr" : row['Email Address'],
                "GivenName" : row['First Name'],
                "FamilyName" : row['Last Name'],
                "PrimaryPhone" : row['Phone']
                }
    return qbo.find_or_create_customer(display_name, customer_attrs)


def parse_vbo_transactions(qbo, payments):
    vbo_transactions_file = data_file("vbo", "transactions_file")
    advance_sale_item = qbo.get_item_by_name("General Admission - Advance")
    door_sale_item = qbo.get_item_by_name("General Admission - Door")
    subscription_sale_item = qbo.get_item_by_name("Ticket Subscription")
    vbo_fees_item = qbo.get_item_by_name("VBO Fees")
    stripe_fees_item = qbo.get_item_by_name("Stripe Fees")
    shows_class = qbo.get_class_by_name("Shows")
    credit_card_receivables_account = qbo.get_account_by_name("Stripe Receivables")

    for row in csv_rows(vbo_transactions_file, skip_rows=CONFIG['vbo']['header_row']):
        doc_number = "VBO-%s" % row['OrderID']
        order_date = datetime.strptime(row['Orders'], "%m/%d/%Y %I:%M:%S %p")
        total = to_dec(row['Total'])
        price = to_dec(row['Price'])
        qty = to_dec(row['Qty'])
        vbo_fee = to_dec(row['VBOFee'])
        credit_card = to_dec(row['CreditCard'])
        try:
            event_date = datetime.strptime(row['Event Date'], "%m/%d/%Y %I:%M:%S %p")
        except ValueError:
            logger.debug("invalid event date %s" % row['Event Date'])
            event_date = None

        logger.debug("doc number is %s" % doc_number)

        if row['ItemDescription'] == "Total:":
            logger.debug("reached end of records")
            break

        if qbo.already_processed(doc_number):
            continue
        elif total == 0.0:
            logger.debug("skipping because comp.")
            continue
        elif (credit_card > 0) and (doc_number not in payments):
            msg = "fee information not available yet, skipping %s" % doc_number
            logger.info(msg)
            continue

        customer = vbo_customer(qbo, row)

        with CreateReceipt(qbo) as receipt:
            receipt.CustomerRef = customer.to_ref()
            receipt.DocNumber = doc_number
            receipt.TxnDate = order_date.strftime("%Y-%m-%d")
            receipt.ClassRef = shows_class.to_ref()

            notes = ["Imported via QBO API from VBO export."]
            if row['Notes']:
                notes.append(row['Notes'])
            note = u"\n".join(notes)
            receipt.PrivateNote = note

            is_door_sale = ("Door" in row['ItemName'])
            if is_door_sale:
                item = door_sale_item
            else:
                if "Advance" in row['ItemName']:
                    item = advance_sale_item
                elif "Pack" in row['ItemName']:
                    item = subscription_sale_item
                else:
                    raise Exception("can't identify product '%s'" % row['ItemName'])

            description =  u"%s; %s" % (row['ItemDescription'], row['Event Name'])
            receipt.Line.append(transaction_line_item(price, description, qty, item, event_date))

            if is_door_sale:
                # VBO fees are not added on top
                pass
            else:
                receipt.Line.append(vendor_unit_fee_line_item(-1 * vbo_fee, qty, vbo_fees_item, order_date))

            if credit_card > 0:
                stripe_fees_line = stripe_fee_line_item(payments, total, doc_number, stripe_fees_item, order_date)
                receipt.Line.append(stripe_fees_line)
                receipt.DepositToAccountRef = credit_card_receivables_account.to_ref()
