from quickbats.config import AUTH
from quickbats.config import CONFIG
from quickbats.config import TOKENS
from quickbooks import Oauth2SessionManager
from quickbooks import QuickBooks
from quickbooks.batch import batch_delete
from quickbooks.objects import Account
from quickbooks.objects import Class
from quickbooks.objects import Customer
from quickbooks.objects import Item
from quickbooks.objects import SalesReceipt
import logging
import traceback

logger = logging.getLogger("quickbats")

class QBO(object):
    def __init__(self):
        self._cache = {}

    def connect(self):
        session_manager = Oauth2SessionManager(
                client_id=AUTH['quickbooks_client_id'],
                client_secret=AUTH['quickbooks_client_secret'],
                access_token=TOKENS['access_token'])
        logger.info("starting session...")
        session_manager.start_session()

        logger.info("initializing QuickBooks client...")
        self.client = QuickBooks(
            session_manager=session_manager,
            company_id=AUTH['realm_id'],
            sandbox=CONFIG['app']['sandbox']
     )

    def get_object_by_name(self, klass, name):
        key = "%s:%s" % (klass.__name__, name)
        if key in self._cache:
            logger.debug("found '%s' in cache, using cache" % key)
            return self._cache[key]

        objects = klass.filter(Name=name, qb=self.client)
        if len(objects) == 0:
            raise Exception("no %s found named %s" % (klass.__name__, name))
        elif len(objects) > 1:
            raise Exception("multiple %s found named %s" % (klass.__name__, name))
        else:
            value = objects[0]
            self._cache[key] = value
            return value

    def get_item_by_name(self, name):
        return self.get_object_by_name(Item, name)

    def get_class_by_name(self, name):
        return self.get_object_by_name(Class, name)

    def get_account_by_name(self, name):
        return self.get_object_by_name(Account, name)

    def find_or_create_customer(self, display_name, customer_attrs):
        key = "%s:%s" % (Customer.__name__, display_name)
        if key in self._cache:
            logger.debug("found '%s' in cache, using cache" % key)
            return self._cache[key]
        existing_customers = Customer.filter(DisplayName = display_name, qb=self.client)
        if len(existing_customers) == 0:
            logger.debug("did not find customer matching '%s'" % display_name)
            logger.debug("creating new customer...")
            new_customer = Customer()
            new_customer.DisplayName = display_name
            for k, v in customer_attrs.items():
                # custom handling for tricky fields
                if k == "PrimaryEmailAddr":
                    new_customer.PrimaryEmailAddr = { "Address" : v }
                elif k == "PrimaryPhone":
                    new_customer.PrimaryPhone = { "FreeFormNumber" : v }
                else:
                    # default action - just assign the attribute
                    setattr(new_customer, k, v)
            logger.debug("about to create new customer '%s'" % str(new_customer))
            new_customer.save(qb=self.client)
            logger.debug("new customer created!")
            return new_customer
        elif len(existing_customers) == 1:
            logger.debug("using existing customer for %s" % display_name)
            value = existing_customers[0]
            self._cache[key] = value
            return value
        else:
            logger.error("non-unique customer display name %s" % display_name)
            raise Exception("shouldn't get here - QBO doesn't allow duplicates")

    def already_processed(self, doc_number):
        existing_receipts = SalesReceipt.filter(DocNumber=doc_number, qb=self.client)
        if len(existing_receipts) == 1:
            logger.debug("sales receipt already exists for %s" % doc_number)
            return True
        elif len(existing_receipts) == 0:
            return False
        else:
            raise Exception("shouldn't get here")

    def DELETE_ALL_SALES_RECEIPTS(self):
        """
        Dangerous method - limited to Sandbox use. REMOVE WHEN DONE TESTING.
        """
        assert AUTH['realm_id'] == CONFIG['app']['sandbox_realm']
        assert CONFIG['app']['sandbox']
        receipts = SalesReceipt.filter(qb=self.client)
        results = batch_delete(receipts, qb=self.client)
        for fault in results.faults:
            for error in fault.Error:
                logger.warn(str(error))

    def save_receipt(self, receipt):
        logger.debug("saving receipt:\n%s" % str(receipt.to_json()))
        try:
            receipt.save(qb=self.client)
        except Exception as e:
            for line in traceback.format_exc().splitlines():
                logger.error(line)
            logger.error(e.detail)

class CreateReceipt(object):
    def __init__(self, qbo):
        self.qbo = qbo

    def __enter__(self):
        self.receipt = SalesReceipt()
        return self.receipt

    def __exit__(self, type, value, traceback):
        self.qbo.save_receipt(self.receipt)
