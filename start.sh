#!/bin/sh
DIR="$( cd "$(dirname "$0")" ; pwd -P )"
SCRIPT="$DIR/mainui.py"
echo Starting Script: $SCRIPT
python3 $SCRIPT