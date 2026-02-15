/etc/bash.bashrc:
  file.managed:
    - source: salt://shell/files/bash.bashrc
    - mode: '0644'
