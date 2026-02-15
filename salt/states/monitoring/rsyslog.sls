# CIS 6.1 — Remove rsyslog (journald-only logging)
# Purging the package stops the service and removes config files.

rsyslog_purged:
  pkg.purged:
    - name: rsyslog
