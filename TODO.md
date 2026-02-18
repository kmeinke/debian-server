# TODO

- [ ] SSH certificate authority: add TrustedUserCAKeys to sshd_config, disable raw authorized_keys auth, consider short-lived certs via Vault SSH secrets engine; optionally combine with FIDO2 sk keys for hardware-enforced two-factor
- [ ] Restrict egress DNS to Quad9 IPs only (9.9.9.9, 149.112.112.112) in nftables — blocks DNS tunneling to attacker-controlled resolvers; expose resolver IPs in firewall pillar
- [ ] Restrict egress SMTP (465/587) to smarthost IP only in nftables — blocks spam relay and exfil to arbitrary SMTP servers; requires stable smarthost IP from provider
- [ ] DNSSEC: configure a local validating resolver (e.g. systemd-resolved with DNSSEC=yes, or unbound) so DNS responses are verified locally rather than trusting Quad9 over cleartext
- [ ] Enable AppArmor: install and enforce profiles, especially for the web server process once added
- [ ] Add systemd service hardening: ProtectSystem=strict, PrivateTmp=true, NoNewPrivileges=true at minimum for long-running services
- [ ] Add web server state: TLS config, security headers, process isolation, document root permissions
- [ ] Configure AIDE for file integrity monitoring (baseline database, daily checks, update strategy after Salt highstate)
- [ ] Harden filesystem mount options per server (CIS 1.1.2): nodev/nosuid/noexec on /tmp, /dev/shm, /var/tmp — requires per-server fstab/LUKS partition layout, not suitable for generic Salt state
- [ ] Configure auditd for system auditing (CIS 6.2): audit rules for privileged commands, file access, user/group changes, network config, session tracking
- [ ] Configure remote logging (CIS 6.1.3.6): forward journald logs to a central log server for retention and alerting
- [ ] Periodic audit: world-writable files/dirs (CIS 7.1.11), unowned files (CIS 7.1.12), SUID/SGID binaries (CIS 7.1.13)
- [ ] Periodic audit: user/group integrity — duplicate UIDs/GIDs/names (CIS 7.2.5–7.2.8), shadow group membership (CIS 7.2.4), orphaned GIDs (CIS 7.2.3)
- [ ] Decide on network/IP management: currently DHCP (cloud hoster handles it). Revisit when moving to a real VM — consider static IP config in Salt.
- [ ] Revisit kernel.panic_on_oops=1 (ANSSI R9) when redundancy/failover is available — deliberately skipped on single-instance setup due to availability risk outweighing security benefit
- [ ] Find a struggle-free way to run the test suite — current pain: WSL background jobs lose PID across shell invocations, `test.py shell` is interactive, SSH port 2222 only available after highstate completes; consider a wrapper script that starts container, waits for SSH, runs highstate, runs compliance checks, tears down — all in one WSL command piped to a log file
