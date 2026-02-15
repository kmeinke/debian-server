systemd-timesyncd:
  pkg.installed: []
  service.running:
    - enable: True
    - onlyif: test -d /run/systemd/system

/etc/systemd/timesyncd.conf:
  file.managed:
    - source: salt://base/files/timesyncd.conf
    - template: jinja
    - watch_in:
      - service: systemd-timesyncd
