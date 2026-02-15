/etc/apt/sources.list:
  file.managed:
    - source: salt://apt/files/sources.list
    - template: jinja
    - mode: '0644'

apt_update:
  cmd.wait:
    - name: apt-get update
    - watch:
      - file: /etc/apt/sources.list
