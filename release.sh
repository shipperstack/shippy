#!/bin/bash

pyinstaller -F main.py
cd dist
mv main shippy-linux-x86_64
