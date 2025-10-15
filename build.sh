#!/usr/bin/env bash
# exit on error
set -o errexit

# Install build essentials
apt-get update && apt-get install -y build-essential

# Install Python dependencies
pip install -r backend/requirements.txt