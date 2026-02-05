"""Service for bulk importing expenses from Excel/CSV."""
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict
from io import BytesIO


class ImportService:
    """Service for importing expenses in bulk."""
    
    @staticmethod
    def create_import_template() -> pd.DataFrame:
        """
        Create an Excel template for bulk import.
        
        Returns:
            DataFrame with template structure
        """
        template_data = {
            'Số tài khoản': ['242001', '242002'],
            'Tên khoản mục': ['Chi phí thuê văn phòng', 'Chi phí bảo hiểm'],
            'Mã chứng từ': ['CT001', 'CT002'],
            'Tổng tiền': [36000000, 24000000],
            'Ngày bắt đầu': ['01/01/2024', '15/02/2024'],
            'Ngày kết thúc': ['31/12/2024', '14/02/2025'],
            'Giá trị đã phân bổ': [0, 5000000],
            'Quý-Năm Quá Khứ': ['', 'Q1/2024'],
            'Tags/Nhãn': ['IT, Software', 'HR'],
            'Ghi chú': ['', 'Lưu ý quan trọng']
        }
        
        return pd.DataFrame(template_data)
    
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
        required_columns = ['Số tài khoản', 'Tên khoản mục', 'Tổng tiền', 
                          'Ngày bắt đầu', 'Ngày kết thúc']
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Thiếu cột bắt buộc: {col}")
        
        if errors:
            return False, errors
        
        # Validate each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 because Excel is 1-indexed and has header
            
            # Check account number
            account = str(row['Số tài khoản'])
            if not account.startswith('242'):
                errors.append(f"Dòng {row_num}: Số tài khoản phải bắt đầu bằng 242")
            
            # Check name
            if pd.isna(row['Tên khoản mục']) or str(row['Tên khoản mục']).strip() == '':
                errors.append(f"Dòng {row_num}: Tên khoản mục không được để trống")
            
            # Check amount
            try:
                amount = float(row['Tổng tiền'])
                if amount <= 0:
                    errors.append(f"Dòng {row_num}: Tổng tiền phải lớn hơn 0")
            except (ValueError, TypeError):
                errors.append(f"Dòng {row_num}: Tổng tiền không hợp lệ")
            
            # Check dates
            try:
                start_date = pd.to_datetime(row['Ngày bắt đầu'], dayfirst=True)
                end_date = pd.to_datetime(row['Ngày kết thúc'], dayfirst=True)
                
                if end_date < start_date:
                    errors.append(f"Dòng {row_num}: Ngày kết thúc phải sau ngày bắt đầu")
            except:
                errors.append(f"Dòng {row_num}: Định dạng ngày không hợp lệ (dùng DD/MM/YYYY)")
        
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
            start_date = pd.to_datetime(row['Ngày bắt đầu'], dayfirst=True).date()
            end_date = pd.to_datetime(row['Ngày kết thúc'], dayfirst=True).date()
            
            # Calculate months
            years = end_date.year - start_date.year
            months = end_date.month - start_date.month
            allocation_months = years * 12 + months
            if end_date.day >= start_date.day:
                allocation_months += 1
            
            # Clean up tags
            tags = str(row.get('Tags/Nhãn', '')).strip() if pd.notna(row.get('Tags/Nhãn')) else None
            note = str(row.get('Ghi chú', '')).strip() if pd.notna(row.get('Ghi chú')) else None

            
            expense = {
                'account_number': str(row['Số tài khoản']).strip(),
                'name': str(row['Tên khoản mục']).strip(),
                'document_code': str(row.get('Mã chứng từ', '')).strip() if pd.notna(row.get('Mã chứng từ')) else None,
                'total_amount': float(row['Tổng tiền']),
                'start_date': start_date,
                'end_date': end_date,
                'sub_code': str(row.get('Mã chi phí phụ', '9995')).strip(),
                'allocation_months': max(1, allocation_months),
                'already_allocated': float(row.get('Giá trị đã phân bổ', 0)) if pd.notna(row.get('Giá trị đã phân bổ')) else 0,
                'past_quarter_year': str(row.get('Quý-Năm Quá Khứ', '')).strip() if pd.notna(row.get('Quý-Năm Quá Khứ')) else None,
                'tags': tags,
                'note': note
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
            
            # Additional columns for template to match parse_import_data expectations
            if 'Mã chi phí phụ' not in template_df.columns:
                template_df['Mã chi phí phụ'] = ['9995', '9996']
            
            # Ensure new columns are present
            if 'Giá trị đã phân bổ' not in template_df.columns:
                template_df['Giá trị đã phân bổ'] = [0, 0]
            if 'Quý-Năm Quá Khứ' not in template_df.columns:
                template_df['Quý-Năm Quá Khứ'] = ['', '']
            if 'Tags/Nhãn' not in template_df.columns:
                template_df['Tags/Nhãn'] = ['', '']
            if 'Ghi chú' not in template_df.columns:
                template_df['Ghi chú'] = ['', '']

            buffer = BytesIO() if output_path is None else output_path
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                template_df.to_excel(writer, sheet_name='Template', index=False)
                
                # Add instructions sheet
                instructions = pd.DataFrame({
                    'Hướng dẫn sử dụng': [
                        '1. Điền thông tin chi phí vào sheet "Template"',
                        '2. Số tài khoản phải bắt đầu bằng 242',
                        '3. Tổng tiền phải là số dương',
                        '4. Ngày theo định dạng DD/MM/YYYY (ví dụ: 01/01/2024)',
                        '5. Ngày kết thúc phải sau ngày bắt đầu',
                        '6. Mã chứng từ là tùy chọn',
                        '7. Mã chi phí phụ (9995 hoặc 9996) là tùy chọn, mặc định là 9995',
                        '8. Sau khi điền xong, upload file vào ứng dụng'
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
