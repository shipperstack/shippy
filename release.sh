#!/bin/bash

# Make sure dist and build are gone
rm -r dist/ build/

# Build
python3 setup.py sdist bdist_wheel


# Upload
if [[ $1 == "-t" ]] ; then
    echo "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
else
    echo "Uploading to PyPI..."
    twine upload dist/*
fi
