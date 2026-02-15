{% set hostname = salt['pillar.get']('network:hostname', 'server') %}
{% set domain = salt['pillar.get']('network:domain', 'localdomain') %}
{% set fqdn = hostname ~ '.' ~ domain %}

set_hostname:
  cmd.run:
    - name: hostnamectl set-hostname {{ hostname }}
    - unless: test "$(hostname)" = "{{ hostname }}"

/etc/hosts:
  file.managed:
    - source: salt://base/files/hosts
    - template: jinja
    - context:
        hostname: {{ hostname }}
        domain: {{ domain }}
        fqdn: {{ fqdn }}
