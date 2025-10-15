#!/usr/bin/env bash
# exit on error
set -o errexit

# Set Python version (optional, but good practice)
python --version

# Upgrade pip and build tools
pip install --upgrade pip wheel setuptools

# Install dependencies
pip install -r backend/requirements.txt