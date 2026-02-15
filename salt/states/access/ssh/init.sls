openssh-server:
  pkg.installed: []

sshd:
  service.running:
    - enable: True
    - onlyif: test -d /run/systemd/system
    - require:
      - pkg: openssh-server

/etc/ssh/sshd_config:
  file.managed:
    - source: salt://access/ssh/files/sshd_config
    - template: jinja
    - mode: '0600'
    - watch_in:
      - service: sshd

# CIS 5.1.3 — SSH host key permissions
ssh_host_ed25519_key:
  file.managed:
    - name: /etc/ssh/ssh_host_ed25519_key
    - mode: '0600'
    - replace: False
    - require:
      - pkg: openssh-server

ssh_host_ed25519_key_pub:
  file.managed:
    - name: /etc/ssh/ssh_host_ed25519_key.pub
    - mode: '0644'
    - replace: False
    - require:
      - pkg: openssh-server
