if exists("g:ue4helper")
  finish
endif
let g:ue4helper=1
let s:save_cpo = &cpo

function! BuildUE4(ue4_dir)
	" call setqflist(s:ue4_errorlogs, 'r')
	cwindow
endfunction
nnoremap <F4> :execute 'term ' . $HOME . '/dotfiles/scripts/ue4_open.bat'<CR>
nnoremap <F5> :execute 'term ' . $HOME . '/dotfiles/scripts/ue4_build.bat'<CR>
nnoremap <F6> :execute 'term ' . $HOME . '/dotfiles/scripts/ue4_project.bat'<CR>
nnoremap <F7> :call BuildUE4('D:/work/UE4/UE_4.22')<CR>

let &cpo = s:save_cpo
unlet s:save_cpo
