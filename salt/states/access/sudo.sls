sudo:
  pkg.installed: []

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
