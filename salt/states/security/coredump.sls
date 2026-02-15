# CIS 1.5.3 — Restrict core dumps

{% set coredump = salt['pillar.get']('kernel:coredump', False) %}

{% if not coredump %}
/etc/security/limits.d/99-coredump.conf:
  file.managed:
    - contents: |
        * hard core 0
    - mode: '0644'
    - makedirs: True

/etc/systemd/coredump.conf.d/99-disable.conf:
  file.managed:
    - contents: |
        [Coredump]
        Storage=none
        ProcessSizeMax=0
    - mode: '0644'
    - makedirs: True
{% else %}
/etc/security/limits.d/99-coredump.conf:
  file.absent: []

/etc/systemd/coredump.conf.d/99-disable.conf:
  file.absent: []
{% endif %}
