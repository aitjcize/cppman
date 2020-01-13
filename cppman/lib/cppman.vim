" cppman.vim
"
" Copyright (C) 2010 -  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
" All Rights reserved.
"
" This program is free software; you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation; either version 3 of the License, or
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
"
" Vim syntax file
" Language:	Man page
" Maintainer:	SungHyun Nam <goweol@gmail.com>
" Modified:	Wei-Ning Huang <aitjcize@gmail.com>
" Previous Maintainer:	Gautam H. Mudunuri <gmudunur@informatica.com>
" Version Info:
" Last Change:	2008 Sep 17

" Additional highlighting by Johannes Tanzler <johannes.tanzler@aon.at>:
"	* manSubHeading
"	* manSynopsis (only for sections 2 and 3)

" For version 5.x: Clear all syntax items
" For version 6.x: Quit when a syntax file was already loaded

setl nonu
setl nornu
setl noma
setl keywordprg=cppman
setl buftype=nofile
noremap <buffer> q :q!<CR>

if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syntax on
syntax case ignore
syntax match  manReference       "[a-z_:+-\*][a-z_:+-~!\*<>()]\+ ([1-9][a-z]\=)"
syntax match  manTitle           "^\w.\+([0-9]\+[a-z]\=).*"
syntax match  manSectionHeading  "^[a-z][a-z_ \-:]*[a-z]$"
syntax match  manSubHeading      "^\s\{3\}[a-z][a-z ]*[a-z]$"
syntax match  manOptionDesc      "^\s*[+-][a-z0-9]\S*"
syntax match  manLongOptionDesc  "^\s*--[a-z0-9-]\S*"

syntax include @cppCode runtime! syntax/cpp.vim
syntax match manCFuncDefinition  display "\<\h\w*\>\s*("me=e-1 contained

syntax region manSynopsis start="^SYNOPSIS"hs=s+8 end="^\u\+\s*$"me=e-12 keepend contains=manSectionHeading,@cppCode,manCFuncDefinition
syntax region manSynopsis start="^EXAMPLE"hs=s+7 end="^       [^ ]"he=s-1 keepend contains=manSectionHeading,@cppCode,manCFuncDefinition

" Define the default highlighting.
" For version 5.7 and earlier: only when not done already
" For version 5.8 and later: only when an item doesn't have highlighting yet
if version >= 508 || !exists("did_man_syn_inits")
  if version < 508
    let did_man_syn_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  HiLink manTitle	    Title
  HiLink manSectionHeading  Statement
  HiLink manOptionDesc	    Constant
  HiLink manLongOptionDesc  Constant
  HiLink manReference	    PreProc
  HiLink manSubHeading      Function
  HiLink manCFuncDefinition Function

  delcommand HiLink
endif

""" Vim Viewer
setl mouse=a
setl colorcolumn=0

let s:old_col = &co

function s:reload()
  setl noro
  setl ma
  echo "Loading..."
  exec "%d"
  exec "0r! cppman --force-columns " . (&co - 2) . " '" . g:page_name . "'"
  setl ro
  setl noma
  setl nomod
endfunction

function Rerender()
  if &co != s:old_col
    let s:old_col = &co
    let save_cursor = getpos(".")
    call s:reload()
    call setpos('.', save_cursor)
  end
endfunction

autocmd VimResized * call Rerender()

let g:stack = []

function LoadNewPage()
  " Save current page to stack
  call add(g:stack, [g:page_name, getpos(".")])
  let g:page_name = expand("<cWORD>")
  setl noro
  setl ma
  call s:reload()
  normal! gg
  setl ro
  setl noma
  setl nomod
endfunction

function BackToPrevPage()
  if len(g:stack) > 0
    let context = g:stack[-1]
    call remove(g:stack, -1)
    let g:page_name = context[0]
    call s:reload()
    call setpos('.', context[1])
  end
endfunction

noremap <buffer> K :call LoadNewPage()<CR>
map <buffer> <CR> K
map <buffer> <C-]> K
map <buffer> <2-LeftMouse> K

noremap <buffer> <C-T> :call BackToPrevPage()<CR>
map <buffer> <RightMouse> <C-T>

let b:current_syntax = "man"
