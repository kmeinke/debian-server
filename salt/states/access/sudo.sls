sudo:
  pkg.installed: []

# CIS 5.2.2 + 5.2.3 — sudo uses pty and logs to file
/etc/sudoers.d/99-cis:
  file.managed:
    - contents: |
        Defaults use_pty
        Defaults logfile="/var/log/sudo.log"
    - mode: '0440'
    - check_cmd: /usr/sbin/visudo -c -f
    - require:
      - pkg: sudo

# CIS 5.2.7 — Restrict su to sudo group
/etc/pam.d/su:
  file.managed:
    - contents: |
        auth required pam_wheel.so use_uid group=sudo
        @include common-auth
        @include common-account
        @include common-session
    - mode: '0644'

{% for username, user in salt['pillar.get']('users', {}).items() %}
{% if user.get('sudo', False) %}

/etc/sudoers.d/{{ username }}:
  file.managed:
    - contents: |
        {{ username }} ALL=(ALL) {{ 'NOPASSWD: ' if user.get('sudo_nopasswd', False) else '' }}ALL
    - mode: '0440'
    - check_cmd: /usr/sbin/visudo -c -f
    - require:
      - pkg: sudo

{% endif %}
{% endfor %}
