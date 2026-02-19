# CIS 1.4.2 / ANSSI R28 R29 — Secure /boot

# ANSSI R29 — restrict /boot directory access to root only
/boot:
  file.directory:
    - user: root
    - group: root
    - mode: '0700'

# ANSSI R29 — restrict grub directory
/boot/grub:
  file.directory:
    - user: root
    - group: root
    - mode: '0700'

# CIS 1.4.2 — grub.cfg must be 0600 root:root
/boot/grub/grub.cfg:
  file.managed:
    - user: root
    - group: root
    - mode: '0600'
    - replace: False

# ANSSI R29 — kernel images, initramfs, symbol maps: 0600 root:root
{% for pattern in ['vmlinuz-*', 'initrd.img-*', 'System.map-*', 'symvers-*'] %}
boot_perms_{{ pattern }}:
  cmd.run:
    - name: |
        find /boot -maxdepth 1 -name '{{ pattern }}' \
          -exec chown root:root {} + \
          -exec chmod 0600 {} +
    - onlyif: find /boot -maxdepth 1 -name '{{ pattern }}' | grep -q .
{% endfor %}

# config-* left at 0644 (kernel build config, low sensitivity)
boot_perms_config:
  cmd.run:
    - name: |
        find /boot -maxdepth 1 -name 'config-*' \
          -exec chown root:root {} + \
          -exec chmod 0644 {} +
    - onlyif: find /boot -maxdepth 1 -name 'config-*' | grep -q .

