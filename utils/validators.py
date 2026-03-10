"""Utility functions for validation."""
import re
from datetime import date


def parse_vn_number(value) -> float:
    """
    Parse số từ nhiều định dạng phổ biến (Excel VN, kế toán, plain).

    Hỗ trợ:
      1.200.000     → 1200000  (VN/EU: dấu . phân ngàn)
      1,200,000     → 1200000  (US: dấu , phân ngàn)
      1.200.000,50  → 1200000.5 (VN: . ngàn, , thập phân)
      1,200,000.50  → 1200000.5 (US: , ngàn, . thập phân)
      1200000       → 1200000  (plain)
      1200000.5     → 1200000.5 (plain decimal)
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    # Bỏ ký hiệu tiền tệ và khoảng trắng
    s = re.sub(r'[\s\u00a0đ₫$€£]|(VND|vnđ|vnd)', '', s, flags=re.IGNORECASE).strip()
    if not s:
        return 0.0

    has_dot   = '.' in s
    has_comma = ',' in s

    if has_dot and has_comma:
        # Xác định cái nào là phân cách thập phân: cái xuất hiện SAU CÙNG
        last_dot   = s.rfind('.')
        last_comma = s.rfind(',')
        if last_dot > last_comma:
            # Dạng US: 1,200,000.50 → bỏ dấu ,
            s = s.replace(',', '')
        else:
            # Dạng VN/EU: 1.200.000,50 → bỏ dấu . rồi đổi , → .
            s = s.replace('.', '').replace(',', '.')

    elif has_dot:
        parts = s.split('.')
        # Nhiều dấu . → tất cả là phân ngàn: 1.200.000
        # Một dấu . với 3 chữ số sau → phân ngàn: 1.200
        # Một dấu . với ≠3 chữ số sau → thập phân: 1.5
        if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3):
            s = s.replace('.', '')  # phân ngàn → bỏ hết
        # else: giữ nguyên (thập phân)

    elif has_comma:
        parts = s.split(',')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3):
            s = s.replace(',', '')  # phân ngàn → bỏ hết
        else:
            s = s.replace(',', '.')  # thập phân → đổi sang .

    try:
        return float(s)
    except ValueError:
        raise ValueError(f"Không thể đọc số: '{value}'")


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
