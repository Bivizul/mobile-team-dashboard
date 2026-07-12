import math
from datetime import date, datetime, timedelta


RUSSIAN_PUBLIC_HOLIDAYS = {
    date(2024, 1, 1),
    date(2024, 1, 2),
    date(2024, 1, 3),
    date(2024, 1, 4),
    date(2024, 1, 5),
    date(2024, 1, 6),
    date(2024, 1, 7),
    date(2024, 1, 8),
    date(2024, 2, 23),
    date(2024, 3, 8),
    date(2024, 5, 1),
    date(2024, 5, 2),
    date(2024, 5, 3),
    date(2024, 5, 4),
    date(2024, 5, 5),
    date(2024, 6, 12),
    date(2024, 11, 4),
    date(2025, 1, 1),
    date(2025, 1, 2),
    date(2025, 1, 3),
    date(2025, 1, 6),
    date(2025, 1, 7),
    date(2025, 1, 8),
    date(2025, 2, 23),
    date(2025, 3, 8),
    date(2025, 5, 1),
    date(2025, 5, 2),
    date(2025, 5, 5),
    date(2025, 6, 12),
    date(2025, 11, 4),
    date(2026, 1, 1),
    date(2026, 1, 2),
    date(2026, 1, 3),
    date(2026, 1, 4),
    date(2026, 1, 5),
    date(2026, 1, 6),
    date(2026, 1, 7),
    date(2026, 1, 8),
    date(2026, 2, 23),
    date(2026, 3, 8),
    date(2026, 5, 1),
    date(2026, 5, 4),
    date(2026, 5, 5),
    date(2026, 6, 12),
    date(2026, 11, 4),
}


def hours(seconds):
    return round(seconds / 3600, 1)


def parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    s_value = str(value).strip()
    if not s_value:
        return None

    # Try ISO format (Jira style: 2024-05-13T10:00:00.000+0000)
    try:
        clean_value = s_value.replace("Z", "+00:00")
        # Python < 3.11 fromisoformat doesn't like +HHMM, it wants +HH:MM
        if len(clean_value) > 19 and (clean_value[-5] == '+' or clean_value[-5] == '-') and clean_value[-3] != ':':
            clean_value = clean_value[:-2] + ":" + clean_value[-2:]
        return datetime.fromisoformat(clean_value).date()
    except (ValueError, IndexError):
        pass

    # Try simple YYYY-MM-DD
    try:
        return datetime.strptime(s_value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def is_russian_public_holiday(day):
    return day in RUSSIAN_PUBLIC_HOLIDAYS


def add_business_days(start_date, business_days):
    if business_days <= 0 or not start_date:
        return start_date

    current_date = start_date
    completed_days = 0

    while completed_days < business_days:
        current_date += timedelta(days=1)
        if current_date.weekday() >= 5 or is_russian_public_holiday(current_date):
            continue
        completed_days += 1

    return current_date


def calculate_feature_deadline(start_date, estimate_hours, working_hours_per_day=8):
    if not start_date:
        return None
    if estimate_hours <= 0:
        return start_date

    business_days = max(1, math.ceil(estimate_hours / working_hours_per_day))
    return add_business_days(start_date, business_days - 1)


def count_business_days(start_date, end_date):
    if not start_date or not end_date:
        return 0
    if start_date > end_date:
        return 0

    business_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5 and not is_russian_public_holiday(current_date):
            business_days += 1
        current_date += timedelta(days=1)
    return business_days
