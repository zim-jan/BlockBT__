import re

with open("backend/tests/test_data/test_data_connector.py", "r") as f:
    content = f.read()

content = content.replace("@patch('app.services.data.yfin_connector", "@patch('app.services.data.yfin_connector.yfin_connector")

with open("backend/tests/test_data/test_data_connector.py", "w") as f:
    f.write(content)
