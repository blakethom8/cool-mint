#!/bin/bash

# Check if a migration message was provided
if [ -z "$1" ]
then
    echo "Error: Please provide a migration message"
    echo "Usage: ./makemigration.sh 'add phone field to contacts'"
    exit 1
fi

# Create a timestamp for the migration name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MESSAGE=$(echo $1 | tr ' ' '_' | tr '[:upper:]' '[:lower:]')

# Create the migration
alembic revision --autogenerate -m "${TIMESTAMP}_${MESSAGE}"

echo "Migration created successfully!"
echo "Remember to:"
echo "1. Review the migration file in app/alembic/versions/"
echo "2. Add any data migrations if needed"
echo "3. Test the migration locally before committing"