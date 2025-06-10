#!/bin/bash

# Navigate to the ResumeFlow directory
cd ResumeFlow

# Activate the virtual environment
source .env/bin/activate

# Check if Poetry is installed, if not install it
if ! command -v poetry &> /dev/null
then
    pip install poetry
fi

# Add the validators package
poetry add validators

# Add the python-dotenv package
poetry add python-dotenv

# Install all dependencies
poetry install

echo "Installation complete!"