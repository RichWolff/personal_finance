import pandas as pd
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

@contextmanager
def database_cnxn(*args, **kwds):
    # Code to acquire resource, e.g.:
    sqliteConnection = sqlite3.connect(DATABASE_FILE)
    try:
        yield sqliteConnection
    finally:
        if (sqliteConnection):
            sqliteConnection.close()


def get_files():
    return sorted(glob.glob(os.path.join(RAW_DIR, TRANSACTION_FILE_PATTERN)))

def load_file(file):
    df = pd.read_csv(file, index_col=False, parse_dates=['date'], infer_datetime_format=True)
    df.columns = ['_'.join(x.lower().split()) for x in df.columns]
    return df


def write_new_transactions(df):
    with database_cnxn() as cnxn:
        df.to_sql('mint_transactions', cnxn, if_exists='append', index=False)
    return None


def read_raw_transactions():
    with database_cnxn() as cnxn:
        df = pd.read_sql('select * from mint_transactions', cnxn, parse_dates='date')
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


def ingest_file(file):
    try:
        df = load_file(file)

        trim_records(
            trim_after_date=df.date.min(),
            trim_before_date=df.date.max()
        )

        write_new_transactions(df)

        res = 0
    except Exception as e:
        res = 1
        print(e)

    return res


def move_file_to_imported(file, folder):
    new_file_name = os.path.join(IMPORT_DIR, file.split('\\')[-1])
    shutil.move(file, new_file_name)
    return None


def ingest_and_move_file(file):
    result = ingest_file(file)
    if result == 0:
        move_file_to_imported(file, folder='imported')
    else:
        move_file_to_imported(file, folder='failed')
    return result

def ingest_all_files():
    return [{file:ingest_and_move_file(file)} for file in get_files()] 