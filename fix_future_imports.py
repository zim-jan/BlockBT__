import os

def fix_future(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    future_lines = []
    other_lines = []

    for line in lines:
        if line.strip().startswith('from __future__ import'):
            future_lines.append(line)
        else:
            other_lines.append(line)

    if future_lines:
        with open(filepath, 'w') as f:
            f.write(''.join(future_lines))
            f.write(''.join(other_lines))

for root, _, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            fix_future(os.path.join(root, file))
