if exists("g:ue4helper")
  finish
endif
let g:ue4helper=1
let s:save_cpo = &cpo
let s:py_path=expand('<sfile>:h:h') . '/python/ue4helper.py'
function! s:UE4Func(arg)
	python3 import sys
	execute 'python3 sys.argv = ["' . a:arg . '"]'
	execute 'py3file ' . s:py_path
endfunction
function! s:VSOpen()
python3 << EOF
import vim
import win32com.client
line = vim.eval("line('.')")
col = vim.eval("col('.')")
filename = vim.eval("expand('%:p')")
dte = win32com.client.GetActiveObject("VisualStudio.DTE")
dte.ItemOperations.OpenFile(filename)
dte.ActiveDocument.Selection.MoveToLineAndOffset(line, col)
EOF
endfunction
command! UE4Build execute 'term python ' . s:py_path . ' --build=Development'
command! UE4BuildDebugGame execute 'term python ' . s:py_path . ' --build=DebugGame'
command! UE4GenerateProject execute 'term python ' . s:py_path  . ' --generateproject'
command! UE4OpenProject execute 'term ++hidden python ' . s:py_path  . ' --openproject=development'
command! UE4OpenProjectDebugGame execute 'term ++hidden python ' . s:py_path  . ' --openproject=-debug'
command! UE4Dumps call s:UE4Func('--dumps') | cwindow
command! UE4FZFProject call s:UE4Func('--fzf=project')
command! UE4FZFEngine call s:UE4Func('--fzf=engine')
command! UE4Info call s:UE4Func('--info')
command! UE4RunSln execute 'term ++hidden python ' . s:py_path . ' --runsln'
command! UE4OpenSln execute 'term ++hidden python ' . s:py_path . ' --opensln'
command! UE4VSOpen call s:VSOpen()
let &cpo = s:save_cpo
unlet s:save_cpo
