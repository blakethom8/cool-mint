#!/bin/bash
# Targeted Contact Sync Runner Script
# This script handles environment setup and runs the targeted sync

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "🎯 Targeted Contact Sync Runner"
echo "=================================="
echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "App directory: $APP_DIR"
echo ""

# Change to the app directory (where .env is located)
cd "$APP_DIR"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the targeted sync script
echo "Running targeted sync with arguments: $@"
python -c "
import sys
import os
sys.path.insert(0, '$PROJECT_ROOT')
sys.path.insert(0, '$APP_DIR')

# Change to app directory for .env loading
os.chdir('$APP_DIR')

# Now run the script
from services.salesforce_files.targeted_sync.targeted_contact_sync_bulk import main
sys.argv = ['targeted_contact_sync_bulk.py'] + '$@'.split()
main()
" 