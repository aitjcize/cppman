#!/bin/bash

AUTHOR='AZ Huang <aitjcize@gmail.com>'

cat << EOF > AUTHORS
Developers
----------
$AUTHOR

Contributors
------------
EOF

git log --all --format='%aN <%cE>' | sort -u | grep -v "$AUTHOR" >> AUTHORS
