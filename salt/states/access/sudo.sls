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
