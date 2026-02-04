"""Utility functions for validation."""
import re
from datetime import date


def validate_account_number(account_number: str) -> tuple[bool, str]:
    """
    Validate account number format (242xxx).
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not account_number:
        return False, "Số tài khoản không được để trống"
    
    if not account_number.startswith('242'):
        return False, "Số tài khoản phải bắt đầu bằng 242"
    
    if len(account_number) != 4:
        return False, "Số tài khoản phải có độ dài đúng 4 ký tự"
    
    if not account_number.isdigit():
        return False, "Số tài khoản chỉ được chứa chữ số"
    
    return True, ""


def validate_amount(amount: float) -> tuple[bool, str]:
    """
    Validate amount is positive.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if amount <= 0:
        return False, "Số tiền phải lớn hơn 0"
    
    return True, ""


def validate_date(date_value: date) -> tuple[bool, str]:
    """
    Validate date is not in the future.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if date_value > date.today():
        return False, "Ngày bắt đầu không được ở tương lai"
    
    return True, ""


def validate_file_type(filename: str, allowed_extensions: list[str] = None) -> tuple[bool, str]:
    """
    Validate file type based on extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (default: pdf, jpg, jpeg, png)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
    
    if not filename:
        return False, "Tên file không được để trống"
    
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if extension not in allowed_extensions:
        return False, f"Chỉ chấp nhận file: {', '.join(allowed_extensions)}"
    
    return True, ""
