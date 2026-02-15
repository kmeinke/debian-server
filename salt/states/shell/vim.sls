vim:
  pkg.installed: []

/etc/vim/vimrc.local:
  file.managed:
    - source: salt://shell/files/vimrc.local
    - mode: '0644'
    - require:
      - pkg: vim

set_default_editor:
  alternatives.set:
    - name: editor
    - path: /usr/bin/vim.basic
    - require:
      - pkg: vim
