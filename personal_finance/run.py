from email_budget import get_chart, send_email, chart_title
from elt.extract import extract_last_n_days
from elt.load import ingest_all_files, get_transactions_by_day, read_raw_budgets
import datetime as dt
import time


def main():
    success = False
    i = 0
    while not success:
        try: 
            etl()
            make_chart_and_email()
            success = True
        except Exception as e:
            i = i + 1
            if i == 3:
                break
            time.sleep(60*3)


def etl():
    extract_last_n_days(30)
    ingest_all_files('transactions')
    ingest_all_files('budget')


def make_chart_and_email():
    today = dt.date.today() - dt.timedelta(1)

    trans = get_transactions_by_day()

    budgets = read_raw_budgets()
    budgets = budgets[
        (budgets['year'] == today.year) &
        (budgets['month'] == today.month)

    ]
    
    var_spend = trans['Variable Spending']
    budget = budgets[budgets['cat'] == 'Variable Spending']['bgt'].iloc[0]
    spend = var_spend.loc[today.day, str(today.year) + '-' + ('0' + str(today.month))[-2:]]
    fig = get_chart(abs(spend), budget, today)
    ImgFileName = f"budget_attainment_charts/wolff_budget_{today.year}-{('0' + str(today.month))[-2:]}-{today.day}.png"
    fig.savefig(ImgFileName, bbox_inches = 'tight', pad_inches = .1)
    print('sending email')
    send_email(chart_title(today), ImgFileName)


if __name__ == '__main__':
    main()
