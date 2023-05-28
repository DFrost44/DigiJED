#!/bin/bash

set -e

git clone https://github.com/DFrost44/DigiJED

cd DigiJED

sudo apt update
sudo apt install python3-virtualenv -y

virtualenv venv

source ./venv/bin/activate

pip install -r requirements.txt
