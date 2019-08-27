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
command! UE4Build execute 'term python ' . s:py_path . ' -build'
command! UE4GenerateProject execute 'term ++close python ' . s:py_path  . ' -generate_project'
command! UE4OpenProject execute 'term ++hidden python ' . s:py_path  . ' -open_project'
command! UE4Dumps call s:UE4Func('-dumps') | cwindow
command! UE4FZFProject call s:UE4Func('-fzf_project')
command! UE4FZFEngine call s:UE4Func('-fzf_engine')
command! VSOpen execute 'term ++hidden python ' . s:py_path . ' -vs_open_file=' . fnameescape(expand('%:p'))
command! RunSln execute 'term ++hidden python ' . s:py_path . ' -run_sln'
command! OpenSln execute 'term ++hidden python ' . s:py_path . ' -open_sln'
let &cpo = s:save_cpo
unlet s:save_cpo
