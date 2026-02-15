# CIS 2.2.x — Remove unwanted client packages

unwanted_client_packages:
  pkg.purged:
    - pkgs:
      - nis
      - rsh-client
      - talk
      - telnet
      - ldap-utils
      - ftp
