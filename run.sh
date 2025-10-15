#!/bin/bash

echo "Starting GenVR Batch Processor..."
echo ""
echo "Checking Python installation..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Launching application..."
python3 main.py

