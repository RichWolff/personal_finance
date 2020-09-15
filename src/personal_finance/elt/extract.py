import datetime as dt
import hashlib
import os
import pandas as pd
import requests
from io import StringIO
from mintapi import Mint

from personal_finance import settings

# Constants
IMPORT_DIR = settings.DIR_DATA_IMPORTED
RAW_DIR = settings.DIR_DATA_RAW
DATABASE_FILE = settings.DATABASE_FILE
TRANSACTION_FILE_PATTERN = settings.TRANSACTION_FILE_PATTERN
MINT_EMAIL = os.getenv('MINT_EMAIL')
MINT_PWD = os.getenv('MINT_PWD')
MINT_MFA_IMAP_ACCOUNT = os.getenv('MINT_MFA_IMAP_ACCOUNT')
MINT_MFA_IMAP_PWD = os.getenv('MINT_MFA_IMAP_PWD')
MINT_MFA_IMAP_SERVER = os.getenv('MINT_MFA_IMAP_SERVER')
MINT_ROOT_URL = 'https://mint.intuit.com'


def load_mint(headless):
    mint = Mint(
        MINT_EMAIL,
        MINT_PWD,
        mfa_method='sms',
        headless=headless,
        mfa_input_callback=None,
        session_path=None,
        imap_account=MINT_MFA_IMAP_ACCOUNT,
        imap_password=MINT_MFA_IMAP_PWD,
        imap_server=MINT_MFA_IMAP_SERVER,
        imap_folder="INBOX",
        wait_for_sync=True,
        wait_for_sync_timeout=600
    )
    return mint


def get_budget(mint):
    ls = []
    budgets = mint.get_budgets()
    for cat in budgets.keys():
        ls.append(pd.DataFrame(budgets[cat]))

    df = pd.concat(ls)
    df.insert(0, 'year', (dt.date.today()-dt.timedelta(1)).year)
    df.insert(1, 'month', (dt.date.today()-dt.timedelta(1)).month)
    return df


def clean_budget(dfs):
    incomeCols = dfs.isIncome is True
    expenseCols = dfs.isExpense is True
    transferCols = dfs.isTransfer is True

    dfs.loc[incomeCols, 'cash_flow_type'] = 'Income'
    dfs.loc[expenseCols, 'cash_flow_type'] = 'Expense'
    dfs.loc[transferCols, 'cash_flow_type'] = 'Transfer'
    dfs.insert(len(dfs.columns), 'over_budget', False)
    dfs.loc[dfs['rbal'] < 0, 'over_budget'] = True
    dfs = dfs[['id', 'cash_flow_type', 'cat', 'bgt', 'amt', 'rbal', 'over_budget']].dropna(subset=['cash_flow_type'])
    dfs.insert(1, 'year', (dt.date.today()-dt.timedelta(1)).year)
    dfs.insert(2, 'month', (dt.date.today()-dt.timedelta(1)).month)
    dfs.insert(0, 'budget_id', dfs[['year', 'month', 'cat']].astype(str).apply('||'.join, axis=1))
    dfs['budget_id'] = dfs['budget_id'].apply(lambda x: hashlib.sha256(x.encode('UTF-8')).hexdigest())
    dfs.reset_index(drop=True, inplace=True)
    return dfs


def extract_transactions(driver, startDate, endDate):
    base_url = f'{MINT_ROOT_URL}/transactionDownload.event?'
    base_url += f'startDate={startDate}'
    base_url += f'&endDate={endDate}'
    base_url += '&query=&queryNew=&offset=0&filterType=cash'

    result = driver.request(method='get', url=base_url)
    if result.status_code != requests.codes.ok:
        raise RuntimeError('Error requesting %r, status = %d' % (base_url, result.status_code))

    buffer = StringIO(result.content.decode('UTF-8'))
    buffer.seek(0)
    df = pd.read_csv(buffer, parse_dates=['Date'], infer_datetime_format=True)
    df.columns = ['_'.join(c.lower().split()) for c in df.columns]
    return df


def last_n_days(mint, days):
    end = dt.date.today() - dt.timedelta(1)
    begin = end - dt.timedelta(days)
    date_format = r'%m/%d/%Y'
    trans = extract_transactions(driver=mint.driver, startDate=begin.strftime(date_format), endDate=end.strftime(date_format))
    return trans.sort_values('date')


def eltBudget(mint):
    budget_date = dt.date.today() - dt.timedelta(1)
    budget = get_budget(mint)
    budget = clean_budget(budget)
    budget_file = f"budget_{budget_date}.csv"
    budget_filename = os.path.join(RAW_DIR, budget_file)
    budget.to_csv(budget_filename, index=False)
    return None


def extract_last_n_days(days: int = 30, headless: bool = False) -> pd.DataFrame:
    try:
        mint = load_mint(headless=headless)
        trans = last_n_days(mint, days=days)
        # Get min / max date in transactions for file name
        min_date, max_date = trans.date.min(), trans.date.max()
        file = f"transactions_{min_date.date()}_{max_date.date()}.csv"
        filename = os.path.join(RAW_DIR, file)
        trans.to_csv(filename, index=False)

        eltBudget(mint)

    finally:
        mint.close()

    return trans
