#!/bin/sh

python=/usr/bin/python

echo "Make sure you had updated the version number in setup.py"

rm -rf dist/
rm -rf *.egg-info/

$python -m build
$python -m twine upload --repository pypi dist/*
