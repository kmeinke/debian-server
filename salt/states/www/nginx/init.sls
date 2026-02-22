{% set nameservers = salt['pillar.get']('network:nameservers', ['9.9.9.9']) %}
{% set log_level = salt['pillar.get']('nginx:log_level', 'notice') %}

nginx:
  pkg.installed: []

/srv/www:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - require:
      - pkg: nginx

/etc/nginx/nginx.conf:
  file.managed:
    - source: salt://www/nginx/files/nginx.conf
    - template: jinja
    - user: root
    - group: root
    - mode: '0640'
    - context:
        nameservers: {{ nameservers | join(' ') }}
        log_level: {{ log_level }}
    - require:
      - pkg: nginx
    - watch_in:
      - service: nginx

/etc/nginx/sites-available/default:
  file.managed:
    - source: salt://www/nginx/files/default-site.conf
    - user: root
    - group: root
    - mode: '0640'
    - require:
      - pkg: nginx
    - watch_in:
      - service: nginx

/etc/nginx/sites-enabled/default:
  file.symlink:
    - target: /etc/nginx/sites-available/default
    - require:
      - file: /etc/nginx/sites-available/default
    - watch_in:
      - service: nginx

# CIS 2.3.1-2.3.2: harden /etc/nginx directory and file permissions
# recurse only user/group — mode is set per-file by file.managed states above
nginx_etc_perms:
  file.directory:
    - name: /etc/nginx
    - user: root
    - group: root
    - mode: '0750'
    - recurse:
      - user
      - group
    - require:
      - pkg: nginx

nginx_service:
  service.running:
    - name: nginx
    - enable: True
    - onlyif: test -d /run/systemd/system
    - require:
      - pkg: nginx
      - file: /etc/nginx/nginx.conf
      - file: /etc/nginx/sites-enabled/default
