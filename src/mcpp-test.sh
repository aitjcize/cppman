#!/bin/bash
./formatter.py | groff -t -Tascii -man | col -b | vim -R -c 'set ft=man | map q :q<CR>' -
