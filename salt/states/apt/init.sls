remove_old_sources_list:
  file.absent:
    - name: /etc/apt/sources.list

/etc/apt/sources.list.d/debian.sources:
  file.managed:
    - source: salt://apt/files/debian.sources
    - template: jinja
    - mode: '0644'

/etc/apt/apt.conf.d/01norecommends:
  file.managed:
    - contents: |
        APT::Install-Recommends "false";
        APT::Install-Suggests "false";
    - mode: '0644'

# CIS 1.2.1.3 — APT GPG key files (0644, root:root)
/etc/apt/trusted.gpg.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - file_mode: '0644'
    - recurse:
      - user
      - group
      - mode

# CIS 1.2.1.8 — APT sources directory (0755, root:root)
/etc/apt/sources.list.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - file_mode: '0644'
    - recurse:
      - user
      - group
      - mode

# CIS 1.2.1.5 — APT auth credentials (0755 dir, 0640 files)
/etc/apt/auth.conf.d:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - file_mode: '0640'
    - makedirs: True
    - recurse:
      - user
      - group
      - mode

apt_update:
  cmd.wait:
    - name: apt-get update
    - watch:
      - file: /etc/apt/sources.list.d/debian.sources
      - file: remove_old_sources_list
