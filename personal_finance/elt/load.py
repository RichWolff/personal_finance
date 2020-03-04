import pandas as pd
import numpy as np
import os, shutil
import sqlite3
import glob
from contextlib import contextmanager

DATA_DIR = os.getenv('MINT_DATA_DIRECTORY')
IMPORT_DIR = os.path.join(DATA_DIR, 'imported')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
FAILED_DIR = os.path.join(DATA_DIR, 'failed')
DATABASE_FILE = os.getenv('MINT_DATABASE_FILE')
TRANSACTION_FILE_PATTERN = 'transactions*.csv'
BUDGET_FILE_PATTERN = 'budget_*.csv'

@contextmanager
def database_cnxn(*args, **kwds):
    # Code to acquire resource, e.g.:
    sqliteConnection = sqlite3.connect(DATABASE_FILE)
    try:
        yield sqliteConnection
    finally:
        if (sqliteConnection):
            sqliteConnection.close()


def get_files(file_pattern):
    return sorted(glob.glob(os.path.join(RAW_DIR, file_pattern)))


def load_file(file, table):
    if table == 'mint_transactions':
        df = pd.read_csv(file, index_col=False, parse_dates=['date'], infer_datetime_format=True)
    elif table == 'mint_budgets':
        df = pd.read_csv(file, index_col=False)

    df.columns = ['_'.join(x.lower().split()) for x in df.columns]
    return df


def write_new_transactions(df, table):
    with database_cnxn() as cnxn:
        df.to_sql(table, cnxn, if_exists='append', index=False)
    return None


def read_raw_transactions():
    with database_cnxn() as cnxn:
        df = pd.read_sql('select * from mint_transactions', cnxn, parse_dates='date')
    return df


def read_raw_budgets():
    with database_cnxn() as cnxn:
        df = pd.read_sql('select * from mint_budgets', cnxn)
    return df


def trim_records(trim_after_date, trim_before_date):
    with database_cnxn() as cnxn:
        delete_query = f"DELETE FROM mint_transactions WHERE date >= '{trim_after_date}' and date <= '{trim_before_date}'"
        try:
            cursor = cnxn.cursor()
            cursor.execute(delete_query)
            cnxn.commit()
        except Exception as e:
            raise e
        finally:
            cursor.close()  


def trim_budget_records(budget_ids: pd.Series):
    with database_cnxn() as cnxn:
        budget_ids = "'"+"','".join(budget_ids.unique())+"'"
        delete_query = f"DELETE FROM mint_budgets WHERE budget_id in ({budget_ids})"
        try:
            cursor = cnxn.cursor()
            cursor.execute(delete_query)
            cnxn.commit()
        except Exception as e:
            raise e
        finally:
            cursor.close()


def ingest_file(file, trim_func, save_table):
    try:
        df = load_file(file, save_table)
        if save_table == 'mint_transactions':
            trim_func(
                trim_after_date=df.date.min(),
                trim_before_date=df.date.max()
            )

        elif save_table == 'mint_budgets':
            trim_func(
                df.budget_id
            )

        write_new_transactions(df, save_table)

        res = 0
    except Exception as e:
        res = 1
        print(e)

    return res


def move_file_to_imported(file, folder):
    new_file_name = os.path.join(folder, file.split('\\')[-1])
    shutil.move(file, new_file_name)
    return None


def ingest_and_move_file(file, trim_func, save_table):
    result = ingest_file(file, trim_func, save_table)
    if result == 0:
        move_file_to_imported(file, IMPORT_DIR)
    else:
        move_file_to_imported(file, FAILED_DIR)
    return result


def ingest_all_files(etl_source):
    if etl_source == 'budget':
        return [{file:ingest_and_move_file(file, trim_budget_records, 'mint_budgets')} for file in get_files(BUDGET_FILE_PATTERN)] 
    elif etl_source == 'transactions':
        return [{file:ingest_and_move_file(file, trim_records, 'mint_transactions')} for file in get_files(TRANSACTION_FILE_PATTERN)] 


def get_transactions_by_day():
    df = read_raw_transactions()
    df.insert(0, 'year', df['date'].dt.year)
    df.insert(1, 'month', ('0'+df['date'].dt.month.astype(str)).str[-2:])
    df.insert(3, 'day', df['date'].dt.day)
    df.insert(4, 'year-month', df.year.astype(str) + '-' + df.month.astype(str))
    df['amount'] = np.where(df['transaction_type'] == 'debit', np.abs(df['amount'])*-1, df['amount'])
    grp = df.groupby(['year-month', 'day', 'category'], as_index=False)['amount'].sum()
    pivotMTD = grp.pivot_table('amount', 'day', ['category', 'year-month'], aggfunc=np.sum).fillna(0).cumsum()
    return pivotMTD