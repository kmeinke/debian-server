fail2ban:
  pkg.installed: []
  service.running:
    - enable: True
    - require:
      - pkg: fail2ban

/etc/fail2ban/jail.local:
  file.managed:
    - source: salt://security/files/jail.local
    - template: jinja
    - mode: '0644'
    - watch_in:
      - service: fail2ban
