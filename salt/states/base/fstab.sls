# ANSSI R28 — mount options for sensitive filesystems

# /boot: nosuid,nodev,noexec
boot_fstab_options:
  mount.mounted:
    - name: /boot
    - persist: True
    - opts: nosuid,nodev,noexec
    - onlyif: mountpoint -q /boot
