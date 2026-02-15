unattended_upgrades_pkgs:
  pkg.installed:
    - pkgs:
      - unattended-upgrades
      - apt-listchanges

/etc/apt/apt.conf.d/50unattended-upgrades:
  file.managed:
    - source: salt://apt/files/50unattended-upgrades
    - template: jinja
    - mode: '0644'

/etc/apt/apt.conf.d/20auto-upgrades:
  file.managed:
    - contents: |
        APT::Periodic::Update-Package-Lists "1";
        APT::Periodic::Unattended-Upgrade "1";
        APT::Periodic::AutocleanInterval "7";
    - mode: '0644'

/etc/apt/listchanges.conf:
  file.managed:
    - source: salt://apt/files/listchanges.conf
    - mode: '0644'
