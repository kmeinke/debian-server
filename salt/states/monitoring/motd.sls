/etc/motd:
  file.managed:
    - source: salt://monitoring/files/motd
    - template: jinja
    - mode: '0644'
