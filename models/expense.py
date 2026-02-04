"""Pydantic models for data validation."""
from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional


class ExpenseCreate(BaseModel):
    """Model for creating a new expense."""
    account_number: str = Field(..., description="Account number in format 242xxx")
    name: str = Field(..., min_length=1, max_length=255, description="Expense name")
    total_amount: float = Field(..., gt=0, description="Total amount (must be positive)")
    start_date: date = Field(..., description="Start date for allocation")
    
    @validator('account_number')
    def validate_account_number(cls, v):
        """Validate account number format (242xxx)."""
        if not v.startswith('242'):
            raise ValueError('Số tài khoản phải bắt đầu bằng 242')
        if len(v) < 4 or len(v) > 10:
            raise ValueError('Số tài khoản phải có độ dài từ 4-10 ký tự')
        if not v.isdigit():
            raise ValueError('Số tài khoản chỉ được chứa chữ số')
        return v


class ExpenseResponse(BaseModel):
    """Model for expense response."""
    id: int
    account_number: str
    name: str
    total_amount: float
    start_date: date
    sub_code: str
    allocation_months: int
    
    class Config:
        from_attributes = True


class AllocationResponse(BaseModel):
    """Model for allocation response."""
    id: int
    expense_id: int
    quarter: int
    year: int
    amount: float
    days_in_quarter: int
    start_date: date
    end_date: date
    
    class Config:
        from_attributes = True
