from quickbooks.objects import SalesItemLine
from quickbats.config import one
from quickbats.config import two_dp
from quickbooks.objects import SalesItemLineDetail
from quickbats.config import logger
from quickbats.config import CONFIG
from decimal import Decimal

stripe_rate = CONFIG['stripe']['rate']
stripe_fixed = CONFIG['stripe']['fixed']
stripe_amex_rate = CONFIG['stripe']['amex_rate']

def transaction_line_item(total, description, qty, item, service_date):
    line = SalesItemLine()
    line.Amount = total
    line.Description = description

    detail = SalesItemLineDetail()
    detail.Qty = qty
    detail.UnitPrice = line.Amount  / detail.Qty
    detail.ItemRef = item.to_ref()
    if service_date:
        detail.ServiceDate = service_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line

def vendor_rate_line_item(total, vendor_rate, vendor_fee_item, order_date):
    line = SalesItemLine()
    line.Amount = (-1) * vendor_rate * total
    line.Description = "{} of {:.1%} of ${:.2f}".format(vendor_fee_item.Name, abs(vendor_rate), total)

    detail = SalesItemLineDetail()
    detail.ItemRef = vendor_fee_item.to_ref()
    detail.Qty = one
    detail.UnitPrice = line.Amount
    detail.ServiceDate = order_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line

def vendor_unit_fee_line_item(vendor_rate, qty, vendor_fee_item, order_date):
    line = SalesItemLine()
    line.Amount = (-1) * vendor_rate * qty
    line.Description = "{} of ${:.2f} x {}".format(vendor_fee_item.Name, abs(vendor_rate), qty)

    detail = SalesItemLineDetail()
    detail.ItemRef = vendor_fee_item.to_ref()
    detail.Qty = qty
    detail.UnitPrice = line.Amount / qty
    detail.ServiceDate = order_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line

def stripe_fee_for_total(total):
    return (total * stripe_rate + stripe_fixed).quantize(two_dp)

def stripe_fee_for_total_amex(total):
    return (total * stripe_amex_rate).quantize(two_dp)

def stripe_fee_line_item(payments, total, payment_id, stripe_fees_item, order_date, other_fees=0):
    payment_info = payments.get(payment_id)
    if payment_info is None:
        return
    total_fee = Decimal(payment_info['Fee'])

    remaining_fee = total_fee - abs(other_fees)
    logger.debug("reconciling remaining fees (after other fees of %s)  %s" % (other_fees, remaining_fee))

    line = SalesItemLine()

    if stripe_fee_for_total(total) == remaining_fee:
        line.Amount = (-1) * stripe_fee_for_total(total)
        line.Description = "Stripe fees of {:.1%} of ${:.2f} plus ${:.2f}".format(stripe_rate, total, stripe_fixed)
    elif stripe_fee_for_total_amex(total) == remaining_fee:
        line.Amount = (-1) * stripe_fee_for_total_amex(total)
        line.Description = "Stripe AmEx fees of {:.1%} of ${:.2f}".format(stripe_amex_rate, total, stripe_fixed)
    else:
        logger.debug("stripe fees of %s don't match standard fees of %s or amex fees of %s" %
                (remaining_fee, stripe_fee_for_total(total), stripe_fee_for_total_amex(total)))
        line.Amount = (-1) * remaining_fee
        line.Description = "Stripe fees"

    detail = SalesItemLineDetail()
    detail.ItemRef = stripe_fees_item.to_ref()
    detail.Qty = one
    detail.UnitPrice = line.Amount
    detail.ServiceDate = order_date.strftime("%Y-%m-%d")

    line.SalesItemLineDetail = detail
    return line
