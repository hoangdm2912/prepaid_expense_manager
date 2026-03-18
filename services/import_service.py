"""Service for bulk importing expenses from Excel/CSV."""
import pandas as pd
from datetime import datetime, date
from typing import List, Tuple, Dict, Any, Optional
from io import BytesIO
from utils.validators import parse_vn_number


class ImportService:
    """Service for importing expenses in bulk."""

    # Tên cột HIỆN TẠI trong template
    COL_ACCOUNT = 'Số tài khoản'
    COL_NAME = 'Tên khoản mục'
    COL_DOC_CODE = 'Mã chứng từ'
    COL_AMOUNT = 'Tổng tiền'
    COL_START = 'Ngày bắt đầu'
    COL_END = 'Ngày kết thúc'
    COL_SEGMENT = 'Segment Ngắn hạn/Dài hạn'
    COL_ALREADY_ALLOC = 'Giá trị đã phân bổ'
    COL_PAST_QY = 'Quý-Năm Quá Khứ'
    COL_TAGS = 'Tags/Nhãn'
    COL_NOTE = 'Ghi chú'

    # Các tên cột thay thế (tên cũ) — để đọc được file template cũ
    COL_SEGMENT_ALIASES = [
        'Segment Ngắn hạn/Dài hạn',
        'Segment (9995/9996)',
        'Segment',
        'Sub Code',
    ]

    @staticmethod
    def create_import_template() -> pd.DataFrame:
        """
        Create an Excel template for bulk import.
        Cột 'Tổng tiền' = tổng GỐC của chứng từ (bao gồm cả phần đã phân bổ quá khứ).
        Hệ thống tự tính phần còn lại = Tổng tiền - Giá trị đã phân bổ.
        """
        template_data = {
            ImportService.COL_ACCOUNT:      ['242001', '242002'],
            ImportService.COL_NAME:         ['Chi phí thuê văn phòng', 'Chi phí bảo hiểm'],
            ImportService.COL_DOC_CODE:     ['CT001', 'CT002'],
            ImportService.COL_AMOUNT:       [36000000, 24000000],
            ImportService.COL_START:        ['01/01/2024', '15/02/2024'],
            ImportService.COL_END:          ['31/12/2024', '14/02/2025'],
            ImportService.COL_SEGMENT:      ['9995', '9996'],
            ImportService.COL_ALREADY_ALLOC:[0, 5000000],
            ImportService.COL_PAST_QY:      ['', 'Q1/2024'],
            ImportService.COL_TAGS:         ['IT, Software', 'HR'],
            ImportService.COL_NOTE:         ['', 'Lưu ý quan trọng'],
        }
        return pd.DataFrame(template_data)

    @staticmethod
    def _find_col(df_or_row, candidates: List[str], default=None):
        """
        Tìm cột đầu tiên tồn tại trong danh sách candidates.
        Trả về (tên_cột, giá_trị_hoặc_None).
        Dùng được với DataFrame (để kiểm tra tên cột) hoặc Series (để đọc giá trị).
        """
        if isinstance(df_or_row, pd.DataFrame):
            for name in candidates:
                if name in df_or_row.columns:
                    return name
            return None
        else:
            # pd.Series (một dòng)
            for name in candidates:
                if name in df_or_row.index:
                    v = df_or_row[name]
                    if not (pd.isna(v) if not isinstance(v, str) else False):
                        return v
            return default

    @staticmethod
    def _get_col(row: pd.Series, col_name: str, default: Any = None) -> Any:
        """Đọc giá trị cột đơn lẻ, trả về default nếu không tồn tại hoặc NaN/empty."""
        if col_name not in row.index:
            return default
        val = row[col_name]
        # Xử lý NaN
        try:
            if pd.isna(val):
                return default
        except (TypeError, ValueError):
            pass
        # Xử lý string rỗng hoặc 'nan'
        if isinstance(val, str) and val.strip().lower() in ('', 'nan', 'none'):
            return default
        return val

    @staticmethod
    def _read_segment(row: pd.Series) -> str:
        """
        Đọc giá trị Segment, hỗ trợ cả tên cột cũ và mới.
        Mặc định 9995 nếu không tìm thấy.
        """
        raw = ImportService._find_col(row, ImportService.COL_SEGMENT_ALIASES, '9995')
        return ImportService._normalize_segment(str(raw))

    @staticmethod
    def _normalize_segment(raw: str) -> str:
        """Chuẩn hóa giá trị segment về '9995' hoặc '9996'."""
        val = str(raw).strip()
        if val in ('9995', 'Ngắn hạn', 'ngan han', 'short', 'NH', 'Short'):
            return '9995'
        if val in ('9996', 'Dài hạn', 'dai han', 'long', 'DH', 'Long'):
            return '9996'
        return val

    @staticmethod
    def validate_import_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate imported data."""
        errors = []

        # Check required columns
        required_columns = [
            ImportService.COL_ACCOUNT,
            ImportService.COL_NAME,
            ImportService.COL_AMOUNT,
            ImportService.COL_START,
            ImportService.COL_END,
        ]
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Thiếu cột bắt buộc: '{col}'")

        if errors:
            return False, errors

        # Kiểm tra tên cột Segment (hỗ trợ tên cũ và mới)
        segment_col_found = ImportService._find_col(df, ImportService.COL_SEGMENT_ALIASES)
        if segment_col_found is None:
            # Không có cột Segment → cảnh báo nhưng không lỗi (default 9995)
            errors.append(
                f"⚠️ Không tìm thấy cột Segment. "
                f"Hệ thống sẽ dùng mặc định '9995' (Ngắn hạn) cho tất cả dòng. "
                f"Tên cột đúng: '{ImportService.COL_SEGMENT}'"
            )

        # Validate từng dòng
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2: Excel 1-indexed + header

            # Account
            account = str(row[ImportService.COL_ACCOUNT]).strip()
            if not account.startswith('242'):
                errors.append(f"Dòng {row_num}: Số tài khoản phải bắt đầu bằng 242")

            # Segment
            segment = ImportService._read_segment(row)
            if segment not in ['9995', '9996']:
                errors.append(
                    f"Dòng {row_num}: Segment phải là 9995 (Ngắn hạn) hoặc 9996 (Dài hạn), "
                    f"giá trị hiện tại: '{segment}'"
                )

            # Name
            if pd.isna(row[ImportService.COL_NAME]) or str(row[ImportService.COL_NAME]).strip() == '':
                errors.append(f"Dòng {row_num}: Tên khoản mục không được để trống")

            # Total amount
            try:
                amount = parse_vn_number(row[ImportService.COL_AMOUNT])
                if amount <= 0:
                    errors.append(f"Dòng {row_num}: Tổng tiền phải lớn hơn 0")
            except (ValueError, TypeError):
                errors.append(f"Dòng {row_num}: Tổng tiền không hợp lệ (giá trị: '{row[ImportService.COL_AMOUNT]}')—định dạng chấp nhận: 1200000 hoặc 1.200.000")

            # Dates
            try:
                start_date = pd.to_datetime(row[ImportService.COL_START], dayfirst=True)
                end_date = pd.to_datetime(row[ImportService.COL_END], dayfirst=True)
                if end_date < start_date:
                    errors.append(f"Dòng {row_num}: Ngày kết thúc phải sau ngày bắt đầu")
            except Exception:
                errors.append(f"Dòng {row_num}: Định dạng ngày không hợp lệ (dùng DD/MM/YYYY)")

            # Already allocated
            raw_alloc = ImportService._get_col(row, ImportService.COL_ALREADY_ALLOC, 0)
            if raw_alloc is not None and raw_alloc != 0:
                try:
                    a = float(raw_alloc)
                    # Kiểm tra already_allocated không vượt quá total_amount
                    try:
                        t = float(row[ImportService.COL_AMOUNT])
                        if a >= t:
                            errors.append(
                                f"Dòng {row_num}: 'Giá trị đã phân bổ' ({a:,.0f}) "
                                f"phải nhỏ hơn 'Tổng tiền' ({t:,.0f})"
                            )
                    except Exception:
                        pass
                except (ValueError, TypeError):
                    errors.append(f"Dòng {row_num}: 'Giá trị đã phân bổ' không hợp lệ")

        # Trả về: nếu chỉ có warning (⚠️) thì vẫn coi là valid
        real_errors = [e for e in errors if not e.startswith('⚠️')]
        return len(real_errors) == 0, errors

    @staticmethod
    def parse_import_data(df: pd.DataFrame) -> List[Dict]:
        """
        Parse validated DataFrame thành list expense records.

        Logic về tiền:
        - 'Tổng tiền' trong XLSX = tổng GỐC của chứng từ
        - 'Giá trị đã phân bổ' = phần đã phân bổ ở quá khứ (trước khi vào hệ thống)
        - Phần còn lại = Tổng tiền - Giá trị đã phân bổ
        - Expense.total_amount = phần CÒN LẠI (sẽ được phân bổ về tương lai)
        - Expense.already_allocated = phần quá khứ
        - Display: Tổng gốc = total_amount + already_allocated ✓
        """
        expenses = []

        for idx, row in df.iterrows():
            start_date = pd.to_datetime(row[ImportService.COL_START], dayfirst=True).date()
            end_date = pd.to_datetime(row[ImportService.COL_END], dayfirst=True).date()

            # Tính số tháng phân bổ
            years  = end_date.year  - start_date.year
            months = end_date.month - start_date.month
            allocation_months = years * 12 + months
            if end_date.day >= start_date.day:
                allocation_months += 1

            # Segment — hỗ trợ cả tên cột cũ lẫn mới
            sub_code = ImportService._read_segment(row)

            # Tags & Note
            raw_tags = ImportService._get_col(row, ImportService.COL_TAGS)
            tags = str(raw_tags).strip() if raw_tags is not None else None

            raw_note = ImportService._get_col(row, ImportService.COL_NOTE)
            note = str(raw_note).strip() if raw_note is not None else None

            # Mã chứng từ
            raw_doc = ImportService._get_col(row, ImportService.COL_DOC_CODE)
            document_code = str(raw_doc).strip() if raw_doc is not None else None

            # --- TIỀN ---
            original_total = parse_vn_number(row[ImportService.COL_AMOUNT])

            raw_alloc = ImportService._get_col(row, ImportService.COL_ALREADY_ALLOC, 0)
            try:
                already_allocated = parse_vn_number(raw_alloc) if raw_alloc is not None else 0.0
            except (ValueError, TypeError):
                already_allocated = 0.0

            # Phần CÒN LẠI → đây là giá trị lưu vào Expense.total_amount
            # và dùng để tính quarterly allocation
            remaining_amount = max(0.0, original_total - already_allocated)

            # --- Quý-Năm Quá Khứ ---
            raw_past_qy = ImportService._get_col(row, ImportService.COL_PAST_QY)
            past_quarter_year = None
            past_periods: List[Dict] = []

            # future_start_date: mặc định = start_date gốc;
            # sẽ được cập nhật = đầu quý TIẾP THEO sau kỳ quá khứ cuối cùng.
            future_start_date = start_date

            if raw_past_qy is not None:
                past_quarter_year = str(raw_past_qy).strip()
                # Hỗ trợ nhiều kỳ ngăn bởi ";" (ví dụ: Q1/2024;Q2/2024)
                for p_str in [p.strip() for p in past_quarter_year.split(';') if p.strip()]:
                    try:
                        if '/' in p_str:
                            q_part, y_part = p_str.split('/', 1)
                            p_q = int(q_part.replace('Q', '').replace('q', '').strip())
                            p_y = int(y_part.strip())
                            past_periods.append({'quarter': p_q, 'year': p_y, 'amount': 0.0})
                    except Exception:
                        pass

            # Phân chia already_allocated đều cho các kỳ quá khứ
            if past_periods and already_allocated > 0:
                per_period = already_allocated / len(past_periods)
                for p in past_periods:
                    p['amount'] = per_period

            # Tính future_start_date = ngày đầu quý TIẾP THEO sau kỳ quá khứ cuối cùng
            # Điều này đảm bảo phần còn lại KHÔNG tạo allocation trùng với kỳ quá khứ.
            # Ví dụ: Quá khứ Q4/2025 → future_start = 01/01/2026
            if past_periods:
                # Tìm kỳ quá khứ LỚN NHẤT (cuối cùng)
                last_past = max(past_periods, key=lambda p: (p['year'], p['quarter']))
                lq, ly = last_past['quarter'], last_past['year']
                # Quý tiếp theo
                if lq == 4:
                    future_start_date = date(ly + 1, 1, 1)
                else:
                    future_start_date = date(ly, lq * 3 + 1, 1)

            expense = {
                'account_number':   str(row[ImportService.COL_ACCOUNT]).strip(),
                'name':             str(row[ImportService.COL_NAME]).strip(),
                'document_code':    document_code,
                # Lưu phần CÒN LẠI vào total_amount
                # (display sẽ hiện total_amount + already_allocated = tổng gốc)
                'total_amount':     remaining_amount,
                'original_total':   original_total,   # chỉ dùng để log/debug
                'start_date':       start_date,
                'end_date':         end_date,
                # Ngày bắt đầu dùng cho calculate_quarterly_allocations (phần còn lại).
                # Nếu có kỳ quá khứ: = đầu quý tiếp theo sau kỳ cuối cùng.
                # Nếu không có quá khứ: = start_date gốc.
                'future_start_date': future_start_date,
                'sub_code':         sub_code,
                'allocation_months': max(1, allocation_months),
                'already_allocated': already_allocated,
                'past_quarter_year': past_quarter_year,
                'past_periods':     past_periods,
                'tags':             tags,
                'note':             note,
            }
            expenses.append(expense)

        return expenses

    @staticmethod
    def export_template(output_path: str = None) -> any:
        """Export template to Excel file or return as buffer."""
        try:
            template_df = ImportService.create_import_template()
            buffer = BytesIO() if output_path is None else output_path

            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                template_df.to_excel(writer, sheet_name='Template', index=False)

                instructions = pd.DataFrame({
                    'Hướng dẫn sử dụng': [
                        '1. Điền thông tin chi phí vào sheet "Template"',
                        '2. Số tài khoản phải bắt đầu bằng 242 (ví dụ: 242001)',
                        '3. [Tổng tiền] = TỔNG GỐC của chứng từ (kể cả phần đã phân bổ quá khứ)',
                        '4. Ngày theo định dạng DD/MM/YYYY (ví dụ: 01/01/2024)',
                        '5. Ngày kết thúc phải sau ngày bắt đầu',
                        '6. [Segment Ngắn hạn/Dài hạn]: 9995 (≤12 tháng) hoặc 9996 (>12 tháng)',
                        '   → Tính tổng thời gian từ quá khứ đến kết thúc để chọn Segment đúng',
                        '7. [Giá trị đã phân bổ]: số tiền đã phân bổ TRƯỚC KHI vào hệ thống',
                        '   → Hệ thống tự tính: Còn lại = Tổng tiền - Giá trị đã phân bổ',
                        '   → Và chỉ phân bổ phần Còn lại về tương lai',
                        '8. [Quý-Năm Quá Khứ]: kỳ đã phân bổ (ví dụ: Q1/2024)',
                        '   → Nhiều kỳ: dùng dấu chấm phẩy (ví dụ: Q1/2024;Q2/2024)',
                        '9. [Tags/Nhãn] và [Ghi chú] là tùy chọn',
                        '10. Sau khi điền xong, upload file vào ứng dụng',
                    ]
                })
                instructions.to_excel(writer, sheet_name='Hướng dẫn', index=False)

            if output_path is None:
                buffer.seek(0)
                return buffer
            return True
        except Exception as e:
            print(f"Error exporting template: {str(e)}")
            return False if output_path else None
