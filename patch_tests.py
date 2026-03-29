import os
import glob
import re

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # app.api.main is now app.main
    content = content.replace('from app.api.main import app', 'from app.main import app')

    # Old DB models from Phase 1 were deleted. We should use Phase 2 models from app.models.orm if needed, or remove tests.
    # The instructions said "Active, correct ORM logic lives in src/blockbt/models/orm.py".
    # And "Discard the old db folder entirely."
    # Let's check what tests exist in test_db and test_integration and if they reference old DB stuff.
    # We will just rewrite the imports if it references old stuff and let it fail or we can just delete tests relying on Phase 1 DB.

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('backend/tests'):
    for file in files:
        if file.endswith('.py'):
            patch_file(os.path.join(root, file))
