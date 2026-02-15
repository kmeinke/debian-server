logrotate:
  pkg.installed: []

/etc/logrotate.conf:
  file.managed:
    - source: salt://monitoring/files/logrotate.conf
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - pkg: logrotate
