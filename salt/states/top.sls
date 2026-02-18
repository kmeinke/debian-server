base:
  '*':
    # Preflight checks
    - base.preflight

    # Base system
    - base.hostname
    - base.locale
    - base.ntp
    - base.network

    # Access & users
    - access.ssh
    - access.users
    - access.sudo

    # Shell & tools
    - shell.bash
    - shell.vim
    - shell.git
    - shell.packages

    # Mail
    - mail.exim4

    # Package management
    - apt
    - apt.unattended-upgrades

    # Security
    - security.firewall
    - security.fail2ban
    - security.sysctl
    - security.coredump
    - security.packages
    - security.cron
    - security.etc-passwd
    - security.banners
    - security.pki

    # Monitoring & logging
    - monitoring.rsyslog
    - monitoring.journald
    - monitoring.logrotate
