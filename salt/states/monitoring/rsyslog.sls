rsyslog:
  pkg.installed: []
  service.running:
    - enable: True
    - onlyif: test -d /run/systemd/system
