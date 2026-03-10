"""Test import_service logic."""
import pandas as pd
import sys
sys.path.insert(0, '.')
from services.import_service import ImportService

df_real = pd.DataFrame({
    ImportService.COL_ACCOUNT:      ['242001'],
    ImportService.COL_NAME:         ['Chi phi bao hiem'],
    ImportService.COL_AMOUNT:       [24000000],
    ImportService.COL_START:        ['15/02/2024'],
    ImportService.COL_END:          ['14/02/2025'],
    'Segment (9995/9996)':          ['9996'],   # ten COT CU
    ImportService.COL_ALREADY_ALLOC:[5000000],
    ImportService.COL_PAST_QY:      ['Q1/2024'],
    ImportService.COL_TAGS:         ['HR'],
    ImportService.COL_NOTE:         ['Note test'],
})

result = ImportService.parse_import_data(df_real)
r = result[0]

print("=== KET QUA PARSE ===")
print(f"sub_code (segment)  : {r['sub_code']}    <- mong doi: 9996")
print(f"already_allocated   : {r['already_allocated']}  <- mong doi: 5000000")
print(f"total_amount        : {r['total_amount']}  <- mong doi: 19000000 (24M - 5M)")
print(f"original_total      : {r['original_total']}  <- mong doi: 24000000")
print(f"past_quarter_year   : {r['past_quarter_year']}   <- mong doi: Q1/2024")
print(f"past_periods        : {r['past_periods']}  <- mong doi: q=1,y=2024,amt=5M")
print(f"tags                : {r['tags']}    <- mong doi: HR")
print(f"note                : {r['note']}  <- mong doi: Note test")
print()
display_total = r['total_amount'] + r['already_allocated']
print(f"Display tong goc    : {display_total}  <- mong doi: 24000000")
print()
all_ok = (
    r['sub_code'] == '9996' and
    r['already_allocated'] == 5000000 and
    r['total_amount'] == 19000000 and
    r['original_total'] == 24000000 and
    r['past_quarter_year'] == 'Q1/2024' and
    len(r['past_periods']) == 1 and r['past_periods'][0]['amount'] == 5000000 and
    display_total == 24000000
)
print("=== KET LUAN ===")
print("TAT CA DUNG!" if all_ok else "CO LOI!")
