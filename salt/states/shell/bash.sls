/etc/bash.bashrc:
  file.managed:
    - source: salt://shell/files/bash.bashrc
    - mode: '0644'

# CIS 7.1.9 — /etc/shells (0644, root:root)
/etc/shells:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - replace: False
