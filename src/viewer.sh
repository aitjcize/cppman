#!/bin/bash
cat $1 | col -b -x | vim -R -c 'set ft=man | map q :q<CR>' -
