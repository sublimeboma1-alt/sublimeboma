import subprocess
import sys

output = []

result0 = subprocess.run(
    [sys.executable, 'manage.py', 'makemigrations', 'frais_scolaires'],
    capture_output=True, text=True, cwd=r'c:\Users\NGALA\Desktop\sublime'
)
output.append('=== Makemigrations ===')
output.append(result0.stdout)
output.append(result0.stderr)

result1 = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', 'frais_scolaires'],
    capture_output=True, text=True, cwd=r'c:\Users\NGALA\Desktop\sublime'
)
output.append('=== Migrate ===')
output.append(result1.stdout)
output.append(result1.stderr)

with open(r'c:\Users\NGALA\Desktop\sublime\migrate_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))