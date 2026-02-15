# CIS 2.4 — Restrict cron and at

cron_packages:
  pkg.installed:
    - pkgs:
      - cron
      - at

/etc/crontab:
  file.managed:
    - mode: '0600'
    - replace: False
    - require:
      - pkg: cron_packages

{% for dir in ['cron.d', 'cron.daily', 'cron.hourly', 'cron.monthly', 'cron.weekly'] %}
/etc/{{ dir }}:
  file.directory:
    - mode: '0700'
{% endfor %}

/etc/cron.allow:
  file.managed:
    - contents: |
        root
    - mode: '0640'

/etc/at.allow:
  file.managed:
    - contents: |
        root
    - mode: '0640'

/etc/cron.deny:
  file.absent: []

/etc/at.deny:
  file.absent: []
