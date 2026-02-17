/etc/bash.bashrc:
  file.managed:
    - source: salt://shell/files/bash.bashrc
    - mode: '0644'

/root/.bashrc:
  file.managed:
    - source: salt://shell/files/bash.bashrc
    - mode: '0644'
    - user: root
    - group: root

/etc/skel/.bashrc:
  file.managed:
    - source: salt://shell/files/bash.bashrc
    - mode: '0644'

{% for username in salt['pillar.get']('users', {}) %}
/home/{{ username }}/.bashrc:
  file.managed:
    - source: salt://shell/files/bash.bashrc
    - mode: '0644'
    - user: {{ username }}
    - group: {{ username }}
    - require:
      - user: {{ username }}
{% endfor %}

/usr/local/bin/peek:
  file.managed:
    - source: salt://shell/files/peek
    - mode: '0755'

# CIS 7.1.9 — /etc/shells (0644, root:root)
/etc/shells:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - replace: False
