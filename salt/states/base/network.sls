/etc/resolv.conf:
  file.managed:
    - source: salt://base/files/resolv.conf
    - template: jinja
