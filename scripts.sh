#!/bin/bash

# Clean previous builds
rm -rf dist/ build/ 
rm -rf *.egg-info

# Build the package
python -m build

# Check the distribution
python -m twine check dist/*

# Publish to PyPI
python -m twine upload dist/*