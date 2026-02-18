# Hourly journal scan for critical kernel and system errors
# Sends mail to root (aliased to admin) if anything severe is found

/etc/cron.hourly/journal-alert:
  file.managed:
    - source: salt://monitoring/files/journal-alert
    - mode: '0700'
    - user: root
    - group: root
