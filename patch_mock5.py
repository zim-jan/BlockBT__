import os

def fix_mock(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    content = content.replace("mocker.patch('blockbt.", "mocker.patch('app.")
    content = content.replace("@patch('blockbt.", "@patch('app.")
    content = content.replace("mocker.patch('app.engine", "mocker.patch('app.services.engine")
    content = content.replace("@patch('app.engine", "@patch('app.services.engine")
    content = content.replace("mocker.patch('app.strategy", "mocker.patch('app.services.strategy")
    content = content.replace("@patch('app.strategy", "@patch('app.services.strategy")
    content = content.replace("mocker.patch('app.connectors", "mocker.patch('app.services.connectors")
    content = content.replace("@patch('app.connectors", "@patch('app.services.connectors")

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('backend/tests'):
    for file in files:
        if file.endswith('.py'):
            fix_mock(os.path.join(root, file))
