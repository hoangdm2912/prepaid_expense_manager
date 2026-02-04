"""Test script for allocation algorithm."""
from datetime import date
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.allocation import AllocationService
from utils.helpers import format_currency, format_quarter

def test_allocation():
    """Test the allocation algorithm with sample data."""
    
    print("=" * 80)
    print("TEST: Thuật toán phân bổ chi phí theo quý")
    print("=" * 80)
    
    # Test case 1: 12 months allocation
    print("\n📊 Test Case 1: Chi phí 36,000,000 VNĐ - 12 tháng")
    print("-" * 80)
    
    total_amount = 36_000_000
    start_date = date(2024, 1, 15)
    allocation_months = 12
    
    # Determine sub-code
    sub_code = AllocationService.determine_sub_code(allocation_months)
    print(f"Mã phụ: {sub_code} ({'≤12 tháng' if sub_code == '9995' else '>12 tháng'})")
    
    # Calculate allocations
    allocations = AllocationService.calculate_quarterly_allocations(
        total_amount=total_amount,
        start_date=start_date,
        allocation_months=allocation_months
    )
    
    # Display results
    print(f"\nNgày bắt đầu: {start_date.strftime('%d/%m/%Y')}")
    print(f"Số tháng: {allocation_months}")
    print(f"Tổng tiền: {format_currency(total_amount)}")
    print(f"\nSố quý phân bổ: {len(allocations)}\n")
    
    print(f"{'Quý':<12} {'Ngày BĐ':<12} {'Ngày KT':<12} {'Số ngày':<10} {'Tỷ lệ':<10} {'Số tiền':<20}")
    print("-" * 80)
    
    total_days = 0
    total_allocated = 0
    
    for alloc in allocations:
        quarter_str = format_quarter(alloc['quarter'], alloc['year'])
        start_str = alloc['start_date'].strftime('%d/%m/%Y')
        end_str = alloc['end_date'].strftime('%d/%m/%Y')
        days = alloc['days_in_quarter']
        percentage = (days / alloc['total_days']) * 100
        amount = alloc['amount']
        
        print(f"{quarter_str:<12} {start_str:<12} {end_str:<12} {days:<10} {percentage:>6.2f}%   {format_currency(amount):<20}")
        
        total_days += days
        total_allocated += amount
    
    print("-" * 80)
    print(f"{'TỔNG CỘNG':<12} {'':<12} {'':<12} {total_days:<10} {'100.00%':<10} {format_currency(total_allocated):<20}")
    
    # Verify
    print(f"\n✅ Kiểm tra:")
    print(f"   - Tổng tiền phân bổ: {format_currency(total_allocated)}")
    print(f"   - Chênh lệch: {format_currency(abs(total_amount - total_allocated))}")
    print(f"   - Chính xác: {'✓' if abs(total_amount - total_allocated) < 1 else '✗'}")
    
    # Test case 2: 18 months allocation
    print("\n" + "=" * 80)
    print("📊 Test Case 2: Chi phí 54,000,000 VNĐ - 18 tháng")
    print("-" * 80)
    
    total_amount2 = 54_000_000
    start_date2 = date(2024, 3, 1)
    allocation_months2 = 18
    
    sub_code2 = AllocationService.determine_sub_code(allocation_months2)
    print(f"Mã phụ: {sub_code2} ({'≤12 tháng' if sub_code2 == '9995' else '>12 tháng'})")
    
    allocations2 = AllocationService.calculate_quarterly_allocations(
        total_amount=total_amount2,
        start_date=start_date2,
        allocation_months=allocation_months2
    )
    
    print(f"\nNgày bắt đầu: {start_date2.strftime('%d/%m/%Y')}")
    print(f"Số tháng: {allocation_months2}")
    print(f"Tổng tiền: {format_currency(total_amount2)}")
    print(f"\nSố quý phân bổ: {len(allocations2)}\n")
    
    print(f"{'Quý':<12} {'Ngày BĐ':<12} {'Ngày KT':<12} {'Số ngày':<10} {'Tỷ lệ':<10} {'Số tiền':<20}")
    print("-" * 80)
    
    total_days2 = 0
    total_allocated2 = 0
    
    for alloc in allocations2:
        quarter_str = format_quarter(alloc['quarter'], alloc['year'])
        start_str = alloc['start_date'].strftime('%d/%m/%Y')
        end_str = alloc['end_date'].strftime('%d/%m/%Y')
        days = alloc['days_in_quarter']
        percentage = (days / alloc['total_days']) * 100
        amount = alloc['amount']
        
        print(f"{quarter_str:<12} {start_str:<12} {end_str:<12} {days:<10} {percentage:>6.2f}%   {format_currency(amount):<20}")
        
        total_days2 += days
        total_allocated2 += amount
    
    print("-" * 80)
    print(f"{'TỔNG CỘNG':<12} {'':<12} {'':<12} {total_days2:<10} {'100.00%':<10} {format_currency(total_allocated2):<20}")
    
    print(f"\n✅ Kiểm tra:")
    print(f"   - Tổng tiền phân bổ: {format_currency(total_allocated2)}")
    print(f"   - Chênh lệch: {format_currency(abs(total_amount2 - total_allocated2))}")
    print(f"   - Chính xác: {'✓' if abs(total_amount2 - total_allocated2) < 1 else '✗'}")
    
    print("\n" + "=" * 80)
    print("✅ Hoàn thành kiểm tra thuật toán phân bổ")
    print("=" * 80)


if __name__ == "__main__":
    test_allocation()
