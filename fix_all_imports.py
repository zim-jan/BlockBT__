import os
import glob
import re

def update_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Simple replacement for blockbt.
    content = content.replace('from blockbt.api', 'from app.api')
    content = content.replace('import blockbt.api', 'import app.api')

    content = content.replace('from blockbt.models.orm', 'from app.models.orm')
    content = content.replace('import blockbt.models.orm', 'import app.models.orm')

    content = content.replace('from blockbt.models.session', 'from app.db.session')
    content = content.replace('import blockbt.models.session', 'import app.db.session')

    content = content.replace('from blockbt.config', 'from app.core.config')
    content = content.replace('import blockbt.config', 'import app.core.config')

    content = content.replace('from blockbt.engine', 'from app.services.engine')
    content = content.replace('import blockbt.engine', 'import app.services.engine')

    content = content.replace('from blockbt.mcp', 'from app.services.mcp')
    content = content.replace('import blockbt.mcp', 'import app.services.mcp')

    content = content.replace('from blockbt.strategy', 'from app.services.strategy')
    content = content.replace('import blockbt.strategy', 'import app.services.strategy')

    content = content.replace('from blockbt.data', 'from app.services.data')
    content = content.replace('import blockbt.data', 'import app.services.data')

    content = content.replace('from blockbt.connectors', 'from app.services.connectors')
    content = content.replace('import blockbt.connectors', 'import app.services.connectors')

    content = content.replace('from blockbt.utils', 'from app.core.utils')
    content = content.replace('import blockbt.utils', 'import app.core.utils')

    # Catch any remaining blockbt imports
    content = content.replace('from blockbt.', 'from app.')
    content = content.replace('import blockbt.', 'import app.')

    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            update_imports(os.path.join(root, file))
