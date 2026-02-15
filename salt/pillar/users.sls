users:
  admin:
    shell: /bin/bash
    groups:
      - sudo
    sudo: True
    sudo_nopasswd: False
    ssh_keys:
      - ssh-ed25519 AAAA... admin@workstation
