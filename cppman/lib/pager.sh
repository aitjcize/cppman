#!/bin/bash
#
# pager.sh
#
# Copyright (C) 2010 - 2016  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This file is part of cppman.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# Script arguments:
#   $1: pager type
#   $2: page path
#   $3: column
#   $4: vim config
#   $5: page name

get_dev_type() {
  local dev=ascii
  local var
  for var in $LC_ALL $LANG; do
    if [ -n "$(printf "%s" "${var}" | sed 's/-//g' | grep -i utf8)" ]; then
      dev=utf8
      break
    fi
  done
  printf "%s" "${dev}"
}

output_dev=$(get_dev_type)

pager_type=$1
page_path=$2
col=$3
vim_config=$4
page_name=$5

render() {
  gunzip -c "$page_path" | \
    groff -t -c -m man -T$output_dev -rLL=${col}n -rLT=${col}n 2>/dev/null
}

remove_escape() {
    local escape=$(printf '\033')
    sed "s/$escape\[[^m]*m//g" | col -x -b
}

if [ -z "$(which groff)" ]; then
  echo "error: groff not found, please install the groff command"
  exit 1
fi

if [ "$pager_type" = "nvim" ]; then
  if ! which nvim >/dev/null 2>&1; then
    pager_type=vim
  fi
fi
if [ "$pager_type" = "vim" ]; then
  if ! which vim >/dev/null 2>&1; then
    if ! which nvim >/dev/null 2>&1; then
      pager_type=nvim
    else
      pager_type=less
    fi
  fi
fi

case $pager_type in
  system)
    [ -z "$PAGER" ] && PAGER=less
    render | $PAGER
    ;;
  vim|nvim)

    render | remove_escape 3<&- | {
      $pager_type -R -c "let g:page_name=\"$page_name\"" -S $vim_config /dev/fd/3 </dev/tty
    } 3<&0
    ;;
  less)
    render | less
    ;;
  pipe)
    render | remove_escape
esac
