from quickbooks.objects import SalesItemLine
from quickbats.config import one
from quickbats.config import two_dp
from quickbooks.objects import SalesItemLineDetail
from quickbats.config import logger
from quickbats.config import CONFIG
from decimal import Decimal
import stripe

stripe_rate = CONFIG['stripe']['rate']
stripe_fixed = CONFIG['stripe']['fixed']
stripe_amex_rate = CONFIG['stripe']['amex_rate']

def transaction_line_item(total, description, qty, item, service_date, qbo_class=None):
    line = SalesItemLine()
    line.Amount = total
    line.Description = description

    detail = SalesItemLineDetail()
    detail.Qty = qty
    detail.UnitPrice = line.Amount  / detail.Qty
    detail.ItemRef = item.to_ref()
    if qbo_class is not None:
        detail.ClassRef = qbo_class.to_ref()
    if service_date:
        detail.ServiceDate = service_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line

def vendor_rate_line_item(total, vendor_rate, vendor_fee_item, order_date, qbo_class=None):
    line = SalesItemLine()
    line.Amount = (-1) * vendor_rate * total
    line.Description = "{} of {:.1%} of ${:.2f}".format(vendor_fee_item.Name, abs(vendor_rate), total)

    detail = SalesItemLineDetail()
    detail.ItemRef = vendor_fee_item.to_ref()
    if qbo_class is not None:
        detail.ClassRef = qbo_class.to_ref()
    detail.Qty = one
    detail.UnitPrice = line.Amount
    detail.ServiceDate = order_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line

def vendor_unit_fee_line_item(vendor_rate, qty, vendor_fee_item, order_date, qbo_class=None):
    line = SalesItemLine()
    line.Amount = (-1) * vendor_rate * qty
    line.Description = "{} of ${:.2f} x {}".format(vendor_fee_item.Name, abs(vendor_rate), qty)

    detail = SalesItemLineDetail()
    detail.ItemRef = vendor_fee_item.to_ref()
    detail.Qty = qty
    detail.UnitPrice = line.Amount / qty
    if qbo_class is not None:
        detail.ClassRef = qbo_class.to_ref()
    detail.ServiceDate = order_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line

def stripe_fee_for_total(total):
    return (total * stripe_rate + stripe_fixed).quantize(two_dp)

def stripe_fee_for_total_amex(total):
    return (total * stripe_amex_rate).quantize(two_dp)

def stripe_fee_line_item(payments, total, payment_id, stripe_fees_item, order_date, other_fees=0, qbo_class=None):
    charge = payments.get(payment_id)
    if charge is None:
        return
    transaction = stripe.BalanceTransaction.retrieve(charge.balance_transaction)

    stripe_fee_info = None
    for fee_info in transaction.fee_details:
        if fee_info.type == 'stripe_fee':
            stripe_fee_info = fee_info
            break
    if stripe_fee_info is None:
        logger.error(str(transaction.fee_details))
        raise Exception("could not find stripe fee in fees")

    stripe_fee_amount = Decimal(stripe_fee_info.amount) / Decimal(100.0)
    logger.debug("stripe fee amount %s" % stripe_fee_amount)
    line = SalesItemLine()

    if stripe_fee_for_total(total) == stripe_fee_amount:
        line.Amount = (-1) * stripe_fee_for_total(total)
        line.Description = "Stripe fees of {:.1%} of ${:.2f} plus ${:.2f}".format(stripe_rate, total, stripe_fixed)
    elif stripe_fee_for_total_amex(total) == stripe_fee_amount:
        line.Amount = (-1) * stripe_fee_for_total_amex(total)
        line.Description = "Stripe AmEx fees of {:.1%} of ${:.2f}".format(stripe_amex_rate, total, stripe_fixed)
    else:
        logger.debug("stripe fees of %s don't match standard fees of %s or amex fees of %s" %
                (stripe_fee_amount, stripe_fee_for_total(total), stripe_fee_for_total_amex(total)))
        line.Amount = (-1) * stripe_fee_amount
        line.Description = "Stripe fees"

    detail = SalesItemLineDetail()
    detail.ItemRef = stripe_fees_item.to_ref()
    detail.Qty = one
    detail.UnitPrice = line.Amount
    if qbo_class is not None:
        detail.ClassRef = qbo_class.to_ref()
    detail.ServiceDate = order_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line
