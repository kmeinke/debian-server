remove_old_sources_list:
  file.absent:
    - name: /etc/apt/sources.list

/etc/apt/sources.list.d/debian.sources:
  file.managed:
    - source: salt://apt/files/debian.sources
    - template: jinja
    - mode: '0644'

apt_update:
  cmd.wait:
    - name: apt-get update
    - watch:
      - file: /etc/apt/sources.list.d/debian.sources
      - file: remove_old_sources_list
