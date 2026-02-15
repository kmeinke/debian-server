exim4:
  pkg.installed:
    - pkgs:
      - exim4-daemon-light
      - mailutils

exim4_service:
  service.running:
    - name: exim4
    - enable: True
    - require:
      - pkg: exim4

/etc/exim4/update-exim4.conf.conf:
  file.managed:
    - source: salt://mail/exim4/files/update-exim4.conf.conf
    - template: jinja
    - mode: '0644'

/etc/exim4/passwd.client:
  file.managed:
    - source: salt://mail/exim4/files/passwd.client
    - template: jinja
    - mode: '0640'
    - user: root
    - group: Debian-exim

update_exim4_config:
  cmd.wait:
    - name: update-exim4.conf
    - watch:
      - file: /etc/exim4/update-exim4.conf.conf
      - file: /etc/exim4/passwd.client
    - watch_in:
      - service: exim4_service

/etc/aliases:
  file.managed:
    - source: salt://mail/exim4/files/aliases
    - template: jinja

newaliases:
  cmd.wait:
    - name: newaliases
    - watch:
      - file: /etc/aliases
