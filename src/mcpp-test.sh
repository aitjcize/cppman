#!/bin/bash
./formatter.py | col -b -x | vim -R -c 'set ft=man | map q :q<CR>' -
