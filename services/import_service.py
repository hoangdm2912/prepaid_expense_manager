"""Service for bulk importing expenses from Excel/CSV."""
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict, Any
from io import BytesIO


class ImportService:
    """Service for importing expenses in bulk."""

    # Tên cột tiêu chuẩn dùng trong template và validate
    # Phải khớp với nhau để đảm bảo nhất quán
    COL_ACCOUNT = 'Số tài khoản'
    COL_NAME = 'Tên khoản mục'
    COL_DOC_CODE = 'Mã chứng từ'
    COL_AMOUNT = 'Tổng tiền'
    COL_START = 'Ngày bắt đầu'
    COL_END = 'Ngày kết thúc'
    # Đổi tên cột Segment để nhất quán với label trong form nhập tay
    COL_SEGMENT = 'Segment Ngắn hạn/Dài hạn'
    COL_ALREADY_ALLOC = 'Giá trị đã phân bổ'
    COL_PAST_QY = 'Quý-Năm Quá Khứ'
    COL_TAGS = 'Tags/Nhãn'
    COL_NOTE = 'Ghi chú'

    @staticmethod
    def create_import_template() -> pd.DataFrame:
        """
        Create an Excel template for bulk import.

        Returns:
            DataFrame with template structure
        """
        template_data = {
            ImportService.COL_ACCOUNT: ['242001', '242002'],
            ImportService.COL_NAME: ['Chi phí thuê văn phòng', 'Chi phí bảo hiểm'],
            ImportService.COL_DOC_CODE: ['CT001', 'CT002'],
            ImportService.COL_AMOUNT: [36000000, 24000000],
            ImportService.COL_START: ['01/01/2024', '15/02/2024'],
            ImportService.COL_END: ['31/12/2024', '14/02/2025'],
            ImportService.COL_SEGMENT: ['9995', '9996'],
            ImportService.COL_ALREADY_ALLOC: [0, 5000000],
            ImportService.COL_PAST_QY: ['', 'Q1/2024'],
            ImportService.COL_TAGS: ['IT, Software', 'HR'],
            ImportService.COL_NOTE: ['', 'Lưu ý quan trọng']
        }

        return pd.DataFrame(template_data)

    @staticmethod
    def _get_col(row: pd.Series, col_name: str, default: Any = None) -> Any:
        """Helper để đọc giá trị cột, trả về default nếu cột không tồn tại hoặc NaN."""
        val = row.get(col_name, default)
        if pd.isna(val) if not isinstance(val, str) else False:
            return default
        return val

    @staticmethod
    def _normalize_segment(raw: str) -> str:
        """Chuẩn hóa giá trị segment về '9995' hoặc '9996'."""
        val = str(raw).strip()
        # Hỗ trợ các cách gõ khác nhau
        if val in ('9995', 'Ngắn hạn', 'ngan han', 'short', 'NH'):
            return '9995'
        if val in ('9996', 'Dài hạn', 'dai han', 'long', 'DH'):
            return '9996'
        return val

    @staticmethod
    def validate_import_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate imported data.

        Args:
            df: DataFrame with imported data

        Returns:
            Tuple of (is_valid, list of error messages)
        """
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

        # Validate each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 because Excel is 1-indexed and has header

            # Check account number
            account = str(row[ImportService.COL_ACCOUNT]).strip()
            if not account.startswith('242'):
                errors.append(f"Dòng {row_num}: Số tài khoản phải bắt đầu bằng 242")

            # Check segment — cột này không bắt buộc (mặc định 9995)
            raw_segment = ImportService._get_col(row, ImportService.COL_SEGMENT, '9995')
            segment = ImportService._normalize_segment(raw_segment)
            if segment not in ['9995', '9996']:
                errors.append(
                    f"Dòng {row_num}: Segment phải là 9995 (Ngắn hạn) hoặc 9996 (Dài hạn), "
                    f"giá trị hiện tại: '{raw_segment}'"
                )

            # Check name
            if pd.isna(row[ImportService.COL_NAME]) or str(row[ImportService.COL_NAME]).strip() == '':
                errors.append(f"Dòng {row_num}: Tên khoản mục không được để trống")

            # Check amount
            try:
                amount = float(row[ImportService.COL_AMOUNT])
                if amount <= 0:
                    errors.append(f"Dòng {row_num}: Tổng tiền phải lớn hơn 0")
            except (ValueError, TypeError):
                errors.append(f"Dòng {row_num}: Tổng tiền không hợp lệ")

            # Check dates
            try:
                start_date = pd.to_datetime(row[ImportService.COL_START], dayfirst=True)
                end_date = pd.to_datetime(row[ImportService.COL_END], dayfirst=True)

                if end_date < start_date:
                    errors.append(f"Dòng {row_num}: Ngày kết thúc phải sau ngày bắt đầu")
            except Exception:
                errors.append(f"Dòng {row_num}: Định dạng ngày không hợp lệ (dùng DD/MM/YYYY)")

            # Validate Giá trị đã phân bổ (nếu có)
            raw_alloc = ImportService._get_col(row, ImportService.COL_ALREADY_ALLOC, 0)
            if raw_alloc is not None and raw_alloc != 0:
                try:
                    float(raw_alloc)
                except (ValueError, TypeError):
                    errors.append(f"Dòng {row_num}: 'Giá trị đã phân bổ' không hợp lệ")

        return len(errors) == 0, errors

    @staticmethod
    def parse_import_data(df: pd.DataFrame) -> List[Dict]:
        """
        Parse validated DataFrame into expense records.

        Args:
            df: Validated DataFrame

        Returns:
            List of expense dictionaries
        """
        expenses = []

        for idx, row in df.iterrows():
            start_date = pd.to_datetime(row[ImportService.COL_START], dayfirst=True).date()
            end_date = pd.to_datetime(row[ImportService.COL_END], dayfirst=True).date()

            # Calculate months
            years = end_date.year - start_date.year
            months = end_date.month - start_date.month
            allocation_months = years * 12 + months
            if end_date.day >= start_date.day:
                allocation_months += 1

            # Segment
            raw_segment = ImportService._get_col(row, ImportService.COL_SEGMENT, '9995')
            sub_code = ImportService._normalize_segment(raw_segment)

            # Tags & Note
            raw_tags = ImportService._get_col(row, ImportService.COL_TAGS)
            tags = str(raw_tags).strip() if raw_tags is not None and str(raw_tags).strip() not in ('', 'nan', 'None') else None

            raw_note = ImportService._get_col(row, ImportService.COL_NOTE)
            note = str(raw_note).strip() if raw_note is not None and str(raw_note).strip() not in ('', 'nan', 'None') else None

            # Mã chứng từ
            raw_doc = ImportService._get_col(row, ImportService.COL_DOC_CODE)
            document_code = str(raw_doc).strip() if raw_doc is not None and str(raw_doc).strip() not in ('', 'nan', 'None') else None

            # Giá trị đã phân bổ
            raw_alloc = ImportService._get_col(row, ImportService.COL_ALREADY_ALLOC, 0)
            try:
                already_allocated = float(raw_alloc) if raw_alloc is not None else 0.0
            except (ValueError, TypeError):
                already_allocated = 0.0

            # Quý-Năm Quá Khứ — hỗ trợ nhiều kỳ ngăn bởi dấu ";"
            # Ví dụ: "Q1/2024;Q2/2024" → 2 kỳ
            raw_past_qy = ImportService._get_col(row, ImportService.COL_PAST_QY)
            past_quarter_year = None
            past_periods = []  # list of (quarter, year, amount) tuples

            if raw_past_qy is not None and str(raw_past_qy).strip() not in ('', 'nan', 'None'):
                past_quarter_year = str(raw_past_qy).strip()

                # Nếu có nhiều kỳ ngăn bởi ";" thì split
                period_strings = [p.strip() for p in past_quarter_year.split(';') if p.strip()]

                for p_str in period_strings:
                    try:
                        if '/' in p_str:
                            q_part, y_part = p_str.split('/')
                            p_q = int(q_part.replace('Q', '').replace('q', '').strip())
                            p_y = int(y_part.strip())
                            # Nếu nhiều kỳ, mỗi kỳ chia đều already_allocated;
                            # Nếu chỉ 1 kỳ, toàn bộ already_allocated gán cho kỳ đó
                            past_periods.append({'quarter': p_q, 'year': p_y})
                    except Exception:
                        pass

            # Phân chia already_allocated đều cho các kỳ (nếu nhiều kỳ)
            if past_periods and already_allocated > 0:
                per_period = already_allocated / len(past_periods)
                for p in past_periods:
                    p['amount'] = per_period
            elif past_periods and already_allocated == 0:
                # Chỉ lưu kỳ, không có amount
                for p in past_periods:
                    p['amount'] = 0.0

            expense = {
                'account_number': str(row[ImportService.COL_ACCOUNT]).strip(),
                'name': str(row[ImportService.COL_NAME]).strip(),
                'document_code': document_code,
                'total_amount': float(row[ImportService.COL_AMOUNT]),
                'start_date': start_date,
                'end_date': end_date,
                'sub_code': sub_code,
                'allocation_months': max(1, allocation_months),
                'already_allocated': already_allocated,
                'past_quarter_year': past_quarter_year,
                'past_periods': past_periods,  # list chi tiết các kỳ quá khứ
                'tags': tags,
                'note': note,
            }

            expenses.append(expense)

        return expenses

    @staticmethod
    def export_template(output_path: str = None) -> any:
        """
        Export template to Excel file or return as buffer.

        Args:
            output_path: Optional path to save template

        Returns:
            Success status (bool) if output_path provided, else BytesIO buffer
        """
        try:
            template_df = ImportService.create_import_template()

            buffer = BytesIO() if output_path is None else output_path

            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                template_df.to_excel(writer, sheet_name='Template', index=False)

                # Add instructions sheet
                instructions = pd.DataFrame({
                    'Hướng dẫn sử dụng': [
                        '1. Điền thông tin chi phí vào sheet "Template"',
                        '2. Số tài khoản phải bắt đầu bằng 242 (ví dụ: 242001)',
                        '3. Tổng tiền phải là số dương',
                        '4. Ngày theo định dạng DD/MM/YYYY (ví dụ: 01/01/2024)',
                        '5. Ngày kết thúc phải sau ngày bắt đầu',
                        '6. Segment Ngắn hạn/Dài hạn: 9995 (≤12 tháng) hoặc 9996 (>12 tháng)',
                        '7. Nếu có dữ liệu phân bổ quá khứ, tính tổng thời gian từ quá khứ để chọn Segment',
                        '8. Giá trị đã phân bổ: Nhập tổng số tiền đã phân bổ trong quá khứ (nếu có)',
                        '9. Quý-Năm Quá Khứ: Nhập kỳ phân bổ quá khứ (ví dụ: Q1/2024)',
                        '   - Nếu có nhiều kỳ, ngăn cách bằng dấu chấm phẩy (ví dụ: Q1/2024;Q2/2024)',
                        '   - Khi nhiều kỳ, hệ thống tự chia đều "Giá trị đã phân bổ" cho từng kỳ',
                        '10. Tags/Nhãn và Ghi chú là tùy chọn (các nhãn ngăn cách bằng dấu phẩy)',
                        '11. Sau khi điền xong, upload file vào ứng dụng',
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
