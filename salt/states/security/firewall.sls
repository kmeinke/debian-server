nftables:
  pkg.installed: []
  service.running:
    - enable: True
    - onlyif: test -d /run/systemd/system

/etc/nftables.conf:
  file.managed:
    - source: salt://security/files/nftables.conf
    - template: jinja
    - mode: '0755'
    - watch_in:
      - service: nftables
