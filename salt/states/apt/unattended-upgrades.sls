unattended_upgrades_pkgs:
  pkg.installed:
    - pkgs:
      - unattended-upgrades
      - apt-listchanges
      - needrestart

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
        APT::Get::AllowUnauthenticated "false";
    - mode: '0644'

/etc/apt/apt.conf.d/40sandbox:
  file.managed:
    - contents: |
        APT::Sandbox::Seccomp "true";
    - mode: '0644'

/etc/needrestart/conf.d/99-autorestart.conf:
  file.managed:
    - contents: |
        $nrconf{restart} = 'a';
    - mode: '0644'
    - makedirs: True
    - require:
      - pkg: unattended_upgrades_pkgs

/etc/apt/listchanges.conf:
  file.managed:
    - source: salt://apt/files/listchanges.conf
    - mode: '0644'
