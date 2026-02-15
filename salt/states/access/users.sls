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
