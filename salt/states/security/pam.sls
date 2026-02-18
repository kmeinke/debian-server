libpam-runtime:
  pkg.installed: []

# CIS 5.3.2 — pam_faillock: lock accounts after repeated failures
/etc/security/faillock.conf:
  file.managed:
    - source: salt://security/files/faillock.conf
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: libpam-runtime

# CIS 5.4.1 — pam_access: restrict login to pillar-defined users only
/etc/security/access.conf:
  file.managed:
    - source: salt://security/files/access.conf
    - template: jinja
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: libpam-runtime

# CIS 5.3.1 — common-auth: enable faillock and disable nullok
/etc/pam.d/common-auth:
  file.managed:
    - source: salt://security/files/pam-common-auth
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: libpam-runtime

# CIS 5.3.1 — common-account: enable pam_access and faillock account check
/etc/pam.d/common-account:
  file.managed:
    - source: salt://security/files/pam-common-account
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: libpam-runtime

# CIS 5.3.1 — common-session: umask and lastlog
/etc/pam.d/common-session:
  file.managed:
    - source: salt://security/files/pam-common-session
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: libpam-runtime

# CIS 1.7.4 — suppress PAM-driven dynamic motd in sshd (motd managed by Salt)
/etc/pam.d/sshd:
  file.managed:
    - source: salt://security/files/pam-sshd
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: libpam-runtime
