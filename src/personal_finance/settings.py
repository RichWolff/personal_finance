import os
from pathlib import Path

DIR_BASE = Path(os.getenv('BASE_DIR'))
DIR_DATA = DIR_BASE / 'data'
DIR_DATA_IMPORTED = DIR_DATA / 'imported'
DIR_DATA_RAW = DIR_DATA / 'raw'
DIR_DATA_FAILED = DIR_DATA / 'failed'
DIR_REPORTS = DIR_BASE / 'reports'

DATABASE_FILE = DIR_DATA / 'database' / 'db.sqlite'

TRANSACTION_FILE_PATTERN = 'transactions*.csv'
BUDGET_FILE_PATTERN = 'budget_*.csv'

MINT_EMAIL = os.getenv('MINT_EMAIL')
MINT_PWD = os.getenv('MINT_PWD')
MINT_MFA_IMAP_ACCOUNT = os.getenv('MINT_MFA_IMAP_ACCOUNT')
MINT_MFA_IMAP_PWD = os.getenv('MINT_MFA_IMAP_PWD')
MINT_MFA_IMAP_SERVER = os.getenv('MINT_MFA_IMAP_SERVER')
