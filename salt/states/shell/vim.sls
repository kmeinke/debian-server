vim:
  pkg.installed: []

/etc/vim/vimrc.local:
  file.managed:
    - source: salt://shell/files/vimrc.local
    - mode: '0644'
    - require:
      - pkg: vim

set_default_editor:
  cmd.run:
    - name: update-alternatives --set editor /usr/bin/vim.basic
    - unless: update-alternatives --query editor | grep -q 'Value:./usr/bin/vim.basic'
    - require:
      - pkg: vim
