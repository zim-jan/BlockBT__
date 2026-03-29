import os

def fix_mock(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    content = content.replace("'blockbt.data", "'app.services.data")

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('backend/tests'):
    for file in files:
        if file.endswith('.py'):
            fix_mock(os.path.join(root, file))
