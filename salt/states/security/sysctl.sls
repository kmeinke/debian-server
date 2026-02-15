/etc/sysctl.d/99-hardening.conf:
  file.managed:
    - source: salt://security/files/99-hardening.conf
    - template: jinja
    - mode: '0644'

/etc/modprobe.d/blacklist-cis.conf:
  file.managed:
    - source: salt://security/files/modprobe-blacklist.conf
    - mode: '0644'
    - makedirs: True

apply_sysctl:
  cmd.wait:
    - name: sysctl --system
    - onlyif: test -d /run/systemd/system
    - watch:
      - file: /etc/sysctl.d/99-hardening.conf
