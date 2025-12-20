
from calendar import monthrange
from datetime import date, datetime, timedelta


def get_current_week():
    today = date.today()
    # Get the first day of the current week
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(days=2)
    # Get the last day of the current week
    end_of_week = start_of_week + timedelta(days=6)

    return start_of_week, end_of_week


def get_last_week():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(days=2)
    # Get the last day of the current week
    end_of_week = start_of_week + timedelta(days=6)

    # Su    btract 7 days to get the start of the previous week
    start_of_last_week = start_of_week - timedelta(days=7)
    # Subtract 7 days to get the end of the previous week
    end_of_last_week = end_of_week - timedelta(days=7)

    return start_of_last_week, end_of_last_week


def get_date_range(time_period):
    today = date.today()
    if time_period == "CE_JOUR":
        return today, today
    if time_period == "SEMAINE_EN_COURS":
        return get_current_week()

    if time_period == "ANNEE_EN_COURS":
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
        return start_date, end_date

    if time_period == "HIERS":
        start_date = today - timedelta(days=1)

        return start_date, start_date
    if time_period == "SEMAINE_PRECEDENTE":
        start_date = today - timedelta(days=1)
        return get_last_week()

    if time_period == "ANNEE_PRECEDENTE":
        start_of_last_year = date(today.year - 1, 1, 1)
        end_of_last_year = date(today.year - 1, 12, 31)
        return start_of_last_year, end_of_last_year
    if time_period == "T1":
        start_of_first_trimester = date(today.year, 1, 1)
        end_of_first_trimester = date(today.year, 3, 31)
        return start_of_first_trimester, end_of_first_trimester
    if time_period == "T2":
        start_of_first_trimester = date(today.year, 4, 1)
        end_of_first_trimester = date(today.year, 6, 30)
        return start_of_first_trimester, end_of_first_trimester
    if time_period == "T3":
        start_of_first_trimester = date(today.year, 7, 1)
        end_of_first_trimester = date(today.year, 9, 30)
        return start_of_first_trimester, end_of_first_trimester
    if time_period == "T4":
        start_of_first_trimester = date(today.year, 10, 1)
        end_of_first_trimester = date(today.year, 12, 31)
        return start_of_first_trimester, end_of_first_trimester
    if time_period == "S1":
        start_of_first_trimester = date(today.year, 1, 1)
        end_of_first_trimester = date(today.year, 6, 30)
        return start_of_first_trimester, end_of_first_trimester
    if time_period == "S2":
        start_of_first_trimester = date(today.year, 7, 1)
        end_of_first_trimester = date(today.year, 12, 31)
        return start_of_first_trimester, end_of_first_trimester

    elif time_period == "MOIS_EN_COURS":
        _, last_day = monthrange(today.year, today.month)
        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, last_day)
        return start_date, end_date

    elif time_period == "MOIS_PRECEDENT":
        today = date.today()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        _, last_day = monthrange(
            last_day_of_last_month.year, last_day_of_last_month.month)

        first_day_of_last_month = last_day_of_last_month.replace(day=1)

        return first_day_of_last_month, last_day_of_last_month

    else:
        raise ValueError(
            "Invalid time period. Use 'this_year' or 'this_month'.")

    return start_date, end_date
