openssh-server:
  pkg.installed: []

sshd:
  service.running:
    - enable: True
    - require:
      - pkg: openssh-server

/etc/ssh/sshd_config:
  file.managed:
    - source: salt://access/ssh/files/sshd_config
    - template: jinja
    - mode: '0644'
    - watch_in:
      - service: sshd
