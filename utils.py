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
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
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