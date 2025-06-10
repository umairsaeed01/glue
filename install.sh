#!/bin/bash

# Navigate to the ResumeFlow directory
cd ResumeFlow

# Get the path to the virtual environment
VENV_PATH=$(poetry env info -p)

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Install Poetry
pip install poetry

# Update dependencies
poetry update


# Install all dependencies
poetry install

# Exit the script
exit 0

echo "Installation complete!"