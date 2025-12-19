#!/bin/bash

AUTHOR='Wei-Ning Huang <aitjcize@gmail.com>'

cat << EOF > AUTHORS
Developers
----------
$AUTHOR

Contributors
------------
EOF

git log --all --format='%aN <%cE>' | \
  egrep -v '(wnhuang|aitjcize)' | \
  sort -u | \
  grep -v "$AUTHOR" >> AUTHORS
