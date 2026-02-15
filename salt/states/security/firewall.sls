nftables:
  pkg.installed: []
  service.running:
    - enable: True

/etc/nftables.conf:
  file.managed:
    - source: salt://security/files/nftables.conf
    - template: jinja
    - mode: '0755'
    - watch_in:
      - service: nftables
