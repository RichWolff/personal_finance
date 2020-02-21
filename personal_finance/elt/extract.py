import os
import datetime as dt
from mintapi import Mint
import requests
import pandas as pd
from io import StringIO

DATA_DIR = os.getenv('MINT_DATA_DIRECTORY')
IMPORT_DIR = os.path.join(DATA_DIR, 'imported')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
DATABASE_FILE = os.getenv('MINT_DATABASE_FILE')
TRANSACTION_FILE_PATTERN = 'transactions*.csv'
MINT_EMAIL = os.getenv('MINT_EMAIL')
MINT_PWD = os.getenv('MINT_PWD')
MINT_MFA_IMAP_ACCOUNT = os.getenv('MINT_MFA_IMAP_ACCOUNT')
MINT_MFA_IMAP_PWD = os.getenv('MINT_MFA_IMAP_PWD')
MINT_MFA_IMAP_SERVER = os.getenv('MINT_MFA_IMAP_SERVER')

def load_mint():
    mint = Mint(
        MINT_EMAIL,
        MINT_PWD,
        mfa_method='email',
        headless=True,
        mfa_input_callback=None,
        session_path=None,
        imap_account=MINT_MFA_IMAP_ACCOUNT,
        imap_password=MINT_MFA_IMAP_PWD,
        imap_server=MINT_MFA_IMAP_SERVER,
        imap_folder="INBOX",
        wait_for_sync=True,
        wait_for_sync_timeout=300
    )
    return mint

def extract_transactions(driver, startDate, endDate):
    base_url = 'https://mint.intuit.com/transactionDownload.event?'
    base_url += f'startDate={startDate}'
    base_url += f'&endDate={endDate}'
    base_url += '&query=&queryNew=&offset=0&filterType=cash'
    
    result = driver.request(method='get', url=base_url)
    if result.status_code != requests.codes.ok:
        raise RuntimeError('Error requesting %r, status = %d' % (url, result.status_code))
    
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

def extract_last_30_days():
    try:
        mint = load_mint()
        trans = last_n_days(mint, days=30)
        # Get min / max date in transactions for file name
        min_date, max_date = trans.date.min(), trans.date.max()
        file = f"transactions_{min_date.date()}_{max_date.date()}.csv"
        filename = os.path.join(RAW_DIR,file)
        trans.to_csv(filename, index=False)
    finally:
        mint.close()

    return trans

def extract_last_365_days():
    try:
        mint = load_mint()
        trans = last_n_days(mint, days=365)
        # Get min / max date in transactions for file name
        min_date, max_date = trans.date.min(), trans.date.max()
        file = f"transactions_{min_date.date()}_{max_date.date()}.csv"
        filename = os.path.join(RAW_DIR,file)
        trans.to_csv(filename, index=False)
    finally:
        mint.close()

    return trans