openssh-client:
  pkg.installed: []

{% for username, user in salt['pillar.get']('users', {}).items() %}

{{ username }}:
  user.present:
    - shell: {{ user.get('shell', '/bin/bash') }}
    - home: /home/{{ username }}
    - createhome: True
    - groups:
      {% for group in user.get('groups', []) %}
      - {{ group }}
      {% endfor %}

# CIS 7.2.9 — Home directory permissions
{{ username }}_home_permissions:
  file.directory:
    - name: /home/{{ username }}
    - user: {{ username }}
    - group: {{ username }}
    - mode: '0750'
    - require:
      - user: {{ username }}

# CIS 7.2.2 — No empty password fields (lock password)
{{ username }}_lock_password:
  cmd.run:
    - name: passwd -l {{ username }}
    - unless: passwd -S {{ username }} | grep -q '^{{ username }} L'
    - require:
      - user: {{ username }}

{% if user.get('ssh_keys') %}
{{ username }}_ssh_keys:
  ssh_auth.manage:
    - user: {{ username }}
    - ssh_keys: {{ user.ssh_keys | json }}
    - require:
      - user: {{ username }}
      - pkg: openssh-client
{% endif %}

{% endfor %}
