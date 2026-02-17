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
    - contents: ''
    - mode: '0644'
    - user: root
    - group: root

/etc/motd:
  file.managed:
    - source: salt://security/files/motd
    - template: jinja
    - mode: '0644'
