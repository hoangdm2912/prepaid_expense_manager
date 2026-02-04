"""Helper utility functions."""
from datetime import date, timedelta
from calendar import monthrange


def get_quarter(date_value: date) -> tuple[int, int]:
    """
    Get quarter and year for a given date.
    
    Args:
        date_value: Date to get quarter for
    
    Returns:
        tuple: (quarter, year)
    """
    quarter = (date_value.month - 1) // 3 + 1
    return quarter, date_value.year


def get_quarter_dates(quarter: int, year: int) -> tuple[date, date]:
    """
    Get start and end dates for a given quarter.
    
    Args:
        quarter: Quarter number (1-4)
        year: Year
    
    Returns:
        tuple: (start_date, end_date)
    """
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    
    start_date = date(year, start_month, 1)
    _, last_day = monthrange(year, end_month)
    end_date = date(year, end_month, last_day)
    
    return start_date, end_date


def get_days_in_range(start: date, end: date) -> int:
    """
    Get number of days between two dates (inclusive).
    
    Args:
        start: Start date
        end: End date
    
    Returns:
        int: Number of days
    """
    return (end - start).days + 1


def format_currency(amount: float) -> str:
    """
    Format amount as Vietnamese currency with comma separator.
    
    Args:
        amount: Amount to format
    
    Returns:
        str: Formatted currency string with comma separators
    """
    # Format with comma as thousands separator
    return f"{amount:,.0f} ₫".replace(',', ',')


def format_quarter(quarter: int, year: int) -> str:
    """
    Format quarter display.
    
    Args:
        quarter: Quarter number (1-4)
        year: Year
    
    Returns:
        str: Formatted quarter string
    """
    return f"Q{quarter}/{year}"


def add_months(start_date: date, months: int) -> date:
    """
    Add months to a date.
    
    Args:
        start_date: Starting date
        months: Number of months to add
    
    Returns:
        date: New date
    """
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, monthrange(year, month)[1])
    return date(year, month, day)
