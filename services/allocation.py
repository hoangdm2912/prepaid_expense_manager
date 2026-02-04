"""Quarterly allocation service with pro-rata calculation."""
from datetime import date
from typing import List, Dict
from utils.helpers import get_quarter, get_quarter_dates, get_days_in_range, add_months


class AllocationService:
    """Service for calculating quarterly allocations."""
    
    @staticmethod
    def calculate_months_between_dates(start_date: date, end_date: date) -> int:
        """
        Calculate number of months between two dates.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            int: Number of months (rounded)
        """
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        # Add 1 if there are remaining days
        if end_date.day >= start_date.day:
            months += 1
        return max(1, months)
    
    @staticmethod
    def determine_sub_code(allocation_months: int) -> str:
        """
        Determine sub-code based on allocation period.
        
        Args:
            allocation_months: Total months for allocation
        
        Returns:
            str: Sub-code (9995 for ≤12 months, 9996 for >12 months)
        """
        return "9995" if allocation_months <= 12 else "9996"
    
    @staticmethod
    def calculate_allocation_months(total_amount: float, start_date: date) -> int:
        """
        Calculate allocation months based on total amount.
        For this implementation, we'll assume a default monthly rate.
        In practice, this could be user-configurable.
        
        Args:
            total_amount: Total amount to allocate
            start_date: Start date
        
        Returns:
            int: Number of months for allocation
        """
        # This is a simplified version - you may want to make this configurable
        # For now, we'll assume user provides this or we calculate based on amount
        # Default: assume 1 million VND per month
        default_monthly_rate = 1_000_000
        months = int(total_amount / default_monthly_rate)
        return max(1, months)  # At least 1 month
    
    @staticmethod
    def calculate_quarterly_allocations(
        total_amount: float,
        start_date: date,
        end_date: date = None,
        allocation_months: int = None,
        already_allocated: float = 0.0,
        past_quarter_year: str = None
    ) -> List[Dict]:
        """
        Calculate quarterly allocations using pro-rata method based on actual days.
        
        Args:
            total_amount: Total amount to allocate
            start_date: Start date for allocation
            end_date: End date for allocation (preferred)
            allocation_months: Total months for allocation (deprecated, for backward compatibility)
            already_allocated: Amount already allocated in the past
            past_quarter_year: Format "QX/YYYY" representing the last allocated quarter
        
        Returns:
            List of allocation dictionaries with quarter details
        """
        # Calculate end date if not provided
        if end_date is None:
            if allocation_months is None:
                raise ValueError("Either end_date or allocation_months must be provided")
            end_date = add_months(start_date, allocation_months)
            # Adjust to last day of previous month
            from datetime import timedelta
            end_date = date(end_date.year, end_date.month, 1) - timedelta(days=1)
        
        # Calculate total days in allocation period
        total_days = get_days_in_range(start_date, end_date)
        
        remaining_amount = total_amount - already_allocated
        
        # Parse past quarter year to filter out past quarters
        past_q = 0
        past_y = 0
        if past_quarter_year and "/" in past_quarter_year:
            try:
                q_part, y_part = past_quarter_year.split("/")
                past_q = int(q_part.replace("Q", "").replace("q", ""))
                past_y = int(y_part)
            except:
                pass

        allocations = []
        current_date = start_date
        
        # All quarters that should have been allocated
        all_potential_allocations = []
        
        while current_date <= end_date:
            quarter, year = get_quarter(current_date)
            quarter_start, quarter_end = get_quarter_dates(quarter, year)
            
            allocation_start = max(current_date, quarter_start)
            allocation_end = min(end_date, quarter_end)
            days_in_quarter = get_days_in_range(allocation_start, allocation_end)
            
            all_potential_allocations.append({
                'quarter': quarter,
                'year': year,
                'days_in_quarter': days_in_quarter,
                'start_date': allocation_start,
                'end_date': allocation_end
            })
            
            # Move to next quarter
            if quarter == 4:
                current_date = date(year + 1, 1, 1)
            else:
                next_quarter_month = (quarter * 3) + 1
                current_date = date(year, next_quarter_month, 1)
        
        # Filter for future quarters only
        future_allocations = []
        if past_y > 0:
            for alloc in all_potential_allocations:
                if alloc['year'] > past_y or (alloc['year'] == past_y and alloc['quarter'] > past_q):
                    future_allocations.append(alloc)
        else:
            future_allocations = all_potential_allocations

        if not future_allocations:
            return []

        # Calculate pro-rata for future quarters based on remaining amount and remaining total days
        future_total_days = sum(a['days_in_quarter'] for a in future_allocations)
        
        result_allocations = []
        for alloc in future_allocations:
            # Calculate amount based on remaining balance pro-rated by days
            quarter_amount = round((alloc['days_in_quarter'] / future_total_days) * remaining_amount)
            
            result_allocations.append({
                'quarter': alloc['quarter'],
                'year': alloc['year'],
                'amount': quarter_amount,
                'days_in_quarter': alloc['days_in_quarter'],
                'start_date': alloc['start_date'],
                'end_date': alloc['end_date'],
                'total_days': total_days
            })
            
        # Fix rounding error for results
        if result_allocations:
            total_result_allocated = sum(a['amount'] for a in result_allocations)
            difference = int(remaining_amount) - total_result_allocated
            result_allocations[-1]['amount'] += difference

        return result_allocations
    
    @staticmethod
    def get_allocation_summary(allocations: List[Dict]) -> Dict:
        """
        Get summary of allocations.
        
        Args:
            allocations: List of allocation dictionaries
        
        Returns:
            Dictionary with summary information
        """
        total_allocated = sum(a['amount'] for a in allocations)
        total_days = sum(a['days_in_quarter'] for a in allocations)
        
        return {
            'total_quarters': len(allocations),
            'total_allocated': round(total_allocated, 2),
            'total_days': total_days,
            'first_quarter': f"Q{allocations[0]['quarter']}/{allocations[0]['year']}" if allocations else None,
            'last_quarter': f"Q{allocations[-1]['quarter']}/{allocations[-1]['year']}" if allocations else None
        }
