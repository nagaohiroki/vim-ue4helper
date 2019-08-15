if exists("g:ue4helper")
  finish
endif
let g:ue4helper=1
let s:save_cpo = &cpo

let s:py_path=expand('<sfile>:h:h') . '/python/ue4helper.py'
function! s:UE4Dumps()
	python3 import sys
	python3 sys.argv = ['-dumps']
	execute 'py3file ' . s:py_path
	call setqflist(s:ue4_dumps, 'r')
	cwindow
endfunction
let s:py_cmd = 'term python ' . s:py_path
command! UE4Build execute s:py_cmd . ' -build'
command! UE4GenerateProject execute s:py_cmd . ' -generate_project'
command! UE4OpenProject execute s:py_cmd . ' -open_project'
command! UE4Dumps call s:UE4Dumps()
let &cpo = s:save_cpo
unlet s:save_cpo
