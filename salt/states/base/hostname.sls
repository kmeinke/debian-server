{% set hostname = salt['pillar.get']('network:hostname', 'server') %}
{% set domain = salt['pillar.get']('network:domain', 'localdomain') %}
{% set fqdn = hostname ~ '.' ~ domain %}

/etc/hostname:
  file.managed:
    - contents: {{ hostname }}
    - mode: '0644'

set_hostname:
  cmd.run:
    - name: hostname {{ hostname }}
    - unless: test "$(hostname)" = "{{ hostname }}"
    - onlyif: test -d /run/systemd/system
    - require:
      - file: /etc/hostname

/etc/hosts:
  file.managed:
    - source: salt://base/files/hosts
    - template: jinja
    - context:
        hostname: {{ hostname }}
        domain: {{ domain }}
        fqdn: {{ fqdn }}
