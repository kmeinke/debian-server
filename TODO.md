# TODO

- [ ] Configure AIDE for file integrity monitoring (baseline database, daily checks, update strategy after Salt highstate)
- [ ] Harden filesystem mount options per server (CIS 1.1.2): nodev/nosuid/noexec on /tmp, /dev/shm, /var/tmp — requires per-server fstab/LUKS partition layout, not suitable for generic Salt state
- [ ] Configure auditd for system auditing (CIS 6.2): audit rules for privileged commands, file access, user/group changes, network config, session tracking
- [ ] Configure remote logging (CIS 6.1.3.6): forward journald logs to a central log server for retention and alerting
