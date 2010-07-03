#!/bin/bash

cat "$2" | gunzip | groff -t -m man -Tascii -rLL=$1n -rLT=$1n | col -b -x | vim -R -c 'set ft=man | map q :q<CR>' -
