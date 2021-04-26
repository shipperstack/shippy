#!/bin/bash

pyinstaller -F main.py
cd dist || exit
mv main shippy-linux-x86_64
