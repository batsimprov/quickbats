from datetime import datetime
from decimal import Decimal
from quickbats.tokens import TOKENS; TOKENS
import decimal
import logging
import os
import yaml

decimal.getcontext().prec = 8

def decimal_constructor(loader, node):
    value = loader.construct_scalar(node)
    return Decimal(value)

yaml.add_constructor(u'!decimal', decimal_constructor)

with open("config-quickbats.yml", 'rb') as f:
    CONFIG = yaml.load(f)

CONFIG['app']['start_date'] = datetime.strptime(CONFIG['app']['start_date_raw'], "%Y-%m-%d")
CONFIG['app']['start_date_timestamp'] = int(CONFIG['app']['start_date'].timestamp())

with open("auth.yml", 'rb') as f:
    AUTH = yaml.load(f)

logger = logging.getLogger("quickbats")
logsdir = CONFIG['app']['logsdir']
os.makedirs(logsdir, exist_ok=True)
logfilepath = os.path.join(logsdir, "debug.log")
h = logging.FileHandler(logfilepath)
h.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
h.setFormatter(formatter)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)

one = Decimal("1.0")
two_dp = Decimal("0.01")
