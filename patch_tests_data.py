import re

with open("backend/tests/test_data/test_data_connector.py", "r") as f:
    content = f.read()

content = content.replace("@patch('app.data", "@patch('app.services.data")

with open("backend/tests/test_data/test_data_connector.py", "w") as f:
    f.write(content)
