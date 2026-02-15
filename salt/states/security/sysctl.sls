/etc/sysctl.d/99-hardening.conf:
  file.managed:
    - source: salt://security/files/99-hardening.conf
    - mode: '0644'

apply_sysctl:
  cmd.wait:
    - name: sysctl --system
    - onlyif: test -d /run/systemd/system
    - watch:
      - file: /etc/sysctl.d/99-hardening.conf
