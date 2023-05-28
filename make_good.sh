#!/bin/bash

echo "Here we go"

set -e

git clone https://github.com/DFrost44/DigiJED

cd DigiJED

sudo apt install python3-virtualenv

virtualenv venv

source ./venv/bin/activate

pip install -r requirenments.txt
