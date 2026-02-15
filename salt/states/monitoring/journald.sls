# CIS 6.1 — Harden systemd-journald

journald_conf_dir:
  file.directory:
    - name: /etc/systemd/journald.conf.d
    - makedirs: True

journald_hardening:
  file.managed:
    - name: /etc/systemd/journald.conf.d/99-hardening.conf
    - source: salt://monitoring/files/99-journald.conf
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - require:
      - file: journald_conf_dir

# CIS 6.1.1.2 — Ensure journal log directory permissions
journald_log_dir:
  file.directory:
    - name: /var/log/journal
    - user: root
    - group: systemd-journal
    - mode: '2750'
    - makedirs: True

journald_restart:
  cmd.run:
    - name: systemctl restart systemd-journald
    - onlyif: test -d /run/systemd/system
    - onchanges:
      - file: journald_hardening
