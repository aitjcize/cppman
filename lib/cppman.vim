" 
"
" Copyright (C) 2010 -  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
" All Rights reserved.
"
" This program is free software; you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation; either version 2 of the License, or
" (at your option) any later version.
"
" This program is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with this program; if not, write to the Free Software Foundation,
" Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"

set ft=man
set nonu
set iskeyword+=:,=,~,[,],>,*
set keywordprg=cppman
map q :q<CR>
syn case ignore
syn match  manReference       "[a-z_:+-\*][a-z_:+-~!\* <>]\+([1-9][a-z]\=)"
syn match  manTitle	      "^\w.\+([0-9]\+[a-z]\=).*"
syn match  manSectionHeading  "^[a-z][a-z_ \-]*[a-z]$"

syntax include @cCode !runtime syntax/cpp.vim
syn match manCFuncDefinition  display "\<\h\w*\>\s*("me=e-1 contained
syn region manSynopsis start="^SYNOPSIS" end="^[A-Z \t]\+$" keepend contains=manSectionHeading,@cCode,manCFuncDefinition
syn region manSynopsis start="^EXAMPLE" end="^       [^ ]"he=s-1 keepend contains=manSectionHeading,@cCode,manCFuncDefinition
