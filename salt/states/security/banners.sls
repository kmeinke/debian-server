# CIS 1.7.1 — Ensure message of the day is configured properly
# CIS 1.7.2 — Ensure local login warning banner is configured properly
# CIS 1.7.3 — Ensure remote login warning banner is configured properly

/etc/issue:
  file.managed:
    - contents: ''
    - mode: '0644'
    - user: root
    - group: root

/etc/issue.net:
  file.managed:
    - source: salt://security/files/issue.net
    - template: jinja
    - mode: '0644'
    - user: root
    - group: root

/etc/motd:
  file.managed:
    - source: salt://security/files/motd
    - template: jinja
    - mode: '0644'

# Root-specific motd — displayed on root login via bashrc (mode 0640, not world-readable)
/etc/motd.root:
  file.managed:
    - source: salt://security/files/motd.root
    - template: jinja
    - mode: '0640'
    - user: root
    - group: root
