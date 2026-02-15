users:
  admin:
    shell: /bin/bash
    groups:
      - sudo
    sudo: True
    sudo_nopasswd: False
    ssh_keys:
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFVU9t1TkiOP9hbOSBe4SY+Itw/ChNqRXHb1HT2OcIwX admin
