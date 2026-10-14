import subprocess, sys

cmd = [sys.executable, '-m', 'pytest', '--collect-only', '-q']
out = subprocess.run(cmd, capture_output=True, text=True, cwd='backend')
lines = out.stdout.splitlines()

pg_files = {
    'test_nta02_national_divipola_foundation.py',
    'test_nta03_catalog_provisioning_architecture.py',
    'test_nta04_national_provisioning_workflow.py',
    'test_nta05_territorial_control_center.py',
    'test_sa01_superadmin_governance.py',
    'test_sa02_technical_operations_portal.py',
}

counts = {}
current_module = None

for line in lines:
    line = line.strip()
    if line.startswith('<Module ') and line.endswith('>'):
        current_module = line[len('<Module '):-1]
        counts[current_module] = 0
    elif (line.startswith('<Coroutine ') or line.startswith('<Function ')) and current_module:
        counts[current_module] += 1

print(f"Total modules: {len(counts)}")
total_collected = sum(counts.values())
print(f"Total tests collected: {total_collected}")

pg_total = sum(counts.get(m, 0) for m in pg_files)
print(f"PostgreSQL Integration tests ({len(pg_files)} files): {pg_total}")
for m in sorted(pg_files):
    print(f"  {m}: {counts.get(m, 0)}")

unit_files = [m for m in counts if m not in pg_files]
unit_total = sum(counts[m] for m in unit_files)
print(f"In-Memory / Unit / Service tests ({len(unit_files)} files): {unit_total}")
inst_count = counts.get('test_institution_provisioning.py', 0)
nta10_count = counts.get('test_nta10_rector_provisioning.py', 0)
db_safety_count = counts.get('test_db_safety.py', 0)
other_count = unit_total - inst_count - nta10_count - db_safety_count

print(f"  test_institution_provisioning.py: {inst_count}")
print(f"  test_nta10_rector_provisioning.py: {nta10_count}")
print(f"  test_db_safety.py: {db_safety_count}")
print(f"  Remaining unit suites ({len(unit_files)-3} files): {other_count}")

print("\nMathematical reconciliation:")
print(f"Prior to DOC-03-R2:")
print(f"  Postgres (83) + Institution (17) + NTA10 (15) + Other unit ({other_count}) = {83 + 17 + 15 + other_count}")
print(f"  Notice: 83 + 621 = 704! In DOC-03-R1, the author wrote '604' instead of '589' (or '621' total unit)!")
print(f"  Specifically, total unit tests was 17 + 15 + {other_count} = {17 + 15 + other_count} = 621.")
print(f"  If you take total unit = 621, and subtract 17 and 15, you get {621 - 17 - 15} = 589.")
print(f"  In DOC-03-R1, the author wrote 604 as a typo or mistook 621 - 17 = 604!")
print(f"  Indeed: 621 - 17 = 604! The author forgot to subtract the 15 from test_nta10!")
print(f"Current after test_db_safety.py:")
print(f"  Postgres: {pg_total}")
print(f"  Unit: {unit_total}")
print(f"  Total: {pg_total + unit_total}")
