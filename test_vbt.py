import sys
from pathlib import Path
vbt_path = Path("/home/przydan/my_project/vectorbt")
if str(vbt_path) not in sys.path:
    sys.path.insert(0, str(vbt_path))

try:
    import vectorbt as vbt
    print("VBT Loaded From:", vbt.__file__)
    print("Has MA:", hasattr(vbt, 'MA'))
except Exception as e:
    print("Error:", e)
    import vectorbt as vbt
    print(vbt)
