import sys
sys.path.insert(0, '.')
import py_compile

py_compile.compile('utils/validators.py', doraise=True)
py_compile.compile('services/import_service.py', doraise=True)
py_compile.compile('app.py', doraise=True)
print('Syntax OK')

from utils.validators import parse_vn_number

cases = [
    ('1.200.000',    1200000),
    ('1,200,000',    1200000),
    ('1.200.000,50', 1200000.5),
    ('1,200,000.50', 1200000.5),
    ('1200000',      1200000),
    ('1.5',          1.5),
    ('36.000.000',   36000000),
    (24000000,       24000000),
    ('5.000.000',    5000000),
]

all_ok = True
for inp, expected in cases:
    result = parse_vn_number(inp)
    ok = abs(result - expected) < 0.01
    status = 'OK' if ok else f'FAIL (got {result}, expected {expected})'
    print(f'  {str(inp):20s} -> {result:>15.2f}  {status}')
    if not ok:
        all_ok = False

print()
print('ALL PASSED' if all_ok else 'SOME TESTS FAILED')
