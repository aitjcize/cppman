#!/bin/bash
cat "$1" | gunzip | groff -t -m man -Tascii | col -b -x | vim -R -c 'set ft=man | map q :q<CR>' -
