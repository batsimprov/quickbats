from quickbats.payments_stripe import parse_stripe_payments

def test_parse_stripe_payments():
    payments = parse_stripe_payments()
    assert isinstance(payments, dict)
    assert len(payments) == 443, len(payments)
