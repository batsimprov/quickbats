from quickbats.config import CONFIG
from quickbats.config import logger
import stripe

stripe.api_key = CONFIG['stripe']['api_key']
limit = CONFIG['stripe']['batch_size']

def iter_charges():
    has_more = True
    last_object_id = None
    created_filter = {'gt' : CONFIG['app']['start_date']}

    while has_more:
        logger.debug("fetching %s more charges from stripe API" % limit)
        charges = stripe.Charge.list(
                created=created_filter,
                limit=limit,
                starting_after=last_object_id
            )
        for charge in charges:
            last_object_id = charge.id
            yield(charge)
        has_more = charges.has_more

def parse_stripe_payments():
    payments = {}

    for charge in iter_charges():
        description = charge.description or ''
        statement_descriptor = charge.statement_descriptor or ''

        # identify transaction type, then store row under some unique payment
        # identifier which we have access to from vendor data
        if "Bats Improv  - #" in description:
            # VBO Transaction
            vbo_id = charge.description[-7:]
            payments["VBO-%s" % vbo_id] = charge
        elif ("BATS Improv Inv" in statement_descriptor) or ("BATS Invoice" in statement_descriptor):
            # Manually generated invoice, not relevant to this process.
            pass
        elif 'purchased_on' in charge.metadata:
            # Vouchercart Transaction
            payments[charge.id] = charge
        elif 'donation' in charge.metadata:
            # Donately Transaction
            payments[charge.id] = charge
        else:
            logger.warn("unable to categorize this Stripe transaction:")
            logger.warn(str(charge))

    return payments
