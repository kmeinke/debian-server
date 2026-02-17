# CIS 1.2.1.7 — System keyrings directory (0755, root:root)
/usr/share/keyrings:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - file_mode: '0644'
    - recurse:
      - user
      - group
      - mode

# CA trust store — enforce root ownership and read-only
/etc/ca-certificates.conf:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - replace: False

/usr/share/ca-certificates:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - file_mode: '0644'
    - recurse:
      - user
      - group
      - mode

/etc/ssl/certs:
  file.directory:
    - user: root
    - group: root
    - mode: '0755'
    - file_mode: '0644'
    - recurse:
      - user
      - group
      - mode

# SSL private key directory (0700, root:root)
/etc/ssl/private:
  file.directory:
    - user: root
    - group: root
    - mode: '0700'
