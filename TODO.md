# TODO

- [ ] Configure AIDE for file integrity monitoring (baseline database, daily checks, update strategy after Salt highstate)
- [ ] Harden filesystem mount options per server (CIS 1.1.2): nodev/nosuid/noexec on /tmp, /dev/shm, /var/tmp — requires per-server fstab/LUKS partition layout, not suitable for generic Salt state
