# CIS 7.1 — System file permissions

# CIS 7.1.1–7.1.4 — passwd/group files (0644, root:root)
{% for file in ['passwd', 'passwd-', 'group', 'group-'] %}
/etc/{{ file }}:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - replace: False
{% endfor %}

# CIS 7.1.5–7.1.8 — shadow/gshadow files (0640, root:shadow)
{% for file in ['shadow', 'shadow-', 'gshadow', 'gshadow-'] %}
/etc/{{ file }}:
  file.managed:
    - user: root
    - group: shadow
    - mode: '0640'
    - replace: False
{% endfor %}

# CIS 7.1.10 — /etc/security/opasswd (0600, root:root)
opasswd_create:
  cmd.run:
    - name: touch /etc/security/opasswd
    - creates: /etc/security/opasswd

/etc/security/opasswd:
  file.managed:
    - user: root
    - group: root
    - mode: '0600'
    - replace: False
    - require:
      - cmd: opasswd_create
