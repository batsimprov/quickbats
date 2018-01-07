from quickbats.payments_stripe import parse_stripe_payments
from quickbats.qbo import QBO
from quickbats.vendor_donately import parse_donately_transactions

qbo = QBO()
qbo.connect()

# qbo.DELETE_ALL_SALES_RECEIPTS()

payments = parse_stripe_payments()
parse_donately_transactions(qbo, payments)
