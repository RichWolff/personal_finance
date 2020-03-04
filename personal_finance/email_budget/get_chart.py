import matplotlib.pyplot as plt
import numpy as np
import calendar


def get_day_suffix(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return suffix


def chart_title(date):
    return f'Wolff Family {calendar.month_name[date.month]} {date.year} Budget Through The {date.day}{get_day_suffix(date.day)}'


def get_chart(current_spend, budget, as_of_date):
    current_day = as_of_date.day
    year = as_of_date.year
    days_in_month = calendar.monthlen(year, as_of_date.month)
    daily_budget = budget/days_in_month
    daily_burn = current_spend/current_day
    as_of = daily_budget*current_day
    days_away_from_budget = (as_of - current_spend) / daily_budget

    c = '#ff6666' if days_away_from_budget < 0 else '#95db96'
    daysAheadBehind = 'Behind' if days_away_from_budget < 0 else 'Ahead'

    fig = plt.figure(figsize=(6, 4), dpi=300)
    ax = plt.subplot2grid((3, 3), (0, 0), colspan=3)

    ax.barh(y=1, width=current_spend, color=c, zorder=2.5)
    ax.set_xlim(0, max(budget, current_spend)*1.25)

    ax.vlines(budget, ax.get_ylim()[0], ax.get_ylim()[1], zorder=2.5)
    ax.vlines(as_of, ax.get_ylim()[0], ax.get_ylim()[1], ls='--', zorder=3.5)
    ax.text(current_spend-200, 1, '${:.0f}'.format(current_spend), rotation=-90, va='center', zorder=2.5)
    ax.text(budget+1, 1, '${:.0f}'.format(budget), rotation=-90, va='center', zorder=2.5)
    ax.set_title(chart_title(as_of_date))
    ax.get_yaxis().set_visible(False)
    ax.xaxis.set_ticks(np.arange(0, ax.get_xlim()[1], 250))
    ax.tick_params(axis='x', which='major', labelsize=8, rotation=45)
    ax.xaxis.grid(color='black', linestyle='dotted', linewidth=1, alpha=.25, zorder=.5)
    

    ax1 = plt.subplot2grid((3, 3), (1, 0))
    ax1.text(.5, .5, '${:.2f}'.format(daily_budget), ha='center', va='center')
    ax1.get_yaxis().set_visible(False)
    ax1.get_xaxis().set_visible(False)
    ax1.set_title('Daily Budget')

    ax2 = plt.subplot2grid((3, 3), (1, 1))
    ax2.text(.5, .5, '${:.2f}'.format(daily_burn), ha='center', va='center')
    ax2.get_yaxis().set_visible(False)
    ax2.get_xaxis().set_visible(False)
    ax2.set_title('Current Daily Spend')

    ax3 = plt.subplot2grid((3, 3), (1, 2))
    ax3.text(.5, .5, '{:.1f}'.format(days_away_from_budget), ha='center', va='center', color=c)
    ax3.get_yaxis().set_visible(False)
    ax3.get_xaxis().set_visible(False)
    ax3.set_title(f'Days {daysAheadBehind} of Budget')

    fig.tight_layout()
    return fig
