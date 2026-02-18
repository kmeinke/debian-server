# server-salt

SaltStack configuration for a Debian Bookworm server, managed via salt-ssh. Tested via Docker.

---

## Directory Structure

### States (`salt/states/`)

```
states/
├── top.sls                          State top file — assigns states to minions
│
├── base/                            Base system configuration
│   ├── preflight.sls                Fail-fast check: secrets pillar must be loaded
│   ├── hostname.sls                 Hostname, /etc/hosts, FQDN
│   ├── locale.sls                   Locale and timezone
│   ├── network.sls                  DNS resolvers (/etc/resolv.conf)
│   ├── ntp.sls                      Time sync via systemd-timesyncd
│   └── files/                       Config templates for base states
│
├── access/                          Access control
│   ├── ssh/
│   │   ├── init.sls                 OpenSSH server, hardened sshd_config
│   │   └── files/sshd_config        sshd_config template
│   ├── users.sls                    System users, groups, SSH keys
│   └── sudo.sls                     Sudoers drop-ins per user
│
├── shell/                           Shell environment and tools
│   ├── bash.sls                     Bashrc for system, root, skel, and pillar users
│   ├── vim.sls                      Vim config, set as default editor
│   ├── git.sls                      Git installation
│   ├── packages.sls                 Common utility packages
│   └── files/                       Config templates (bash.bashrc, vimrc.local)
│
├── mail/                            Mail delivery
│   └── exim4/
│       ├── init.sls                 Exim4 send-only smarthost setup
│       └── files/                   exim4 config, passwd.client, aliases
│
├── apt/                             Package management
│   ├── init.sls                     APT sources, no-recommends, trust chain permissions
│   ├── unattended-upgrades.sls      Auto security updates, apt-listchanges
│   └── files/                       Config templates
│
├── security/                        Hardening
│   ├── firewall.sls                 nftables — default deny ingress and egress
│   ├── fail2ban.sls                 Brute-force protection for SSH
│   ├── sysctl.sls                   Kernel hardening (sysctl.d)
│   ├── pam.sls                      PAM: faillock, access control, umask, lastlog
│   ├── etc-passwd.sls               Auth file permissions, remove unused users
│   ├── banners.sls                  Login banners: issue.net, motd, motd.root
│   ├── pki.sls                      Keyring, CA trust store, SSL permissions
│   └── files/                       nftables.conf, faillock.conf, access.conf,
│                                    pam-*, 99-hardening.conf, motd, motd.root,
│                                    issue.net
│
└── monitoring/                      Logging and alerting
    ├── rsyslog.sls                  Purge rsyslog (journald-only)
    ├── journald.sls                 Harden systemd-journald (CIS 6.1)
    ├── logrotate.sls                Log rotation
    ├── alerts.sls                   Hourly journal alert cron
    └── files/
        ├── 99-journald.conf         journald hardening config (Jinja)
        ├── logrotate.conf           logrotate base config
        └── journal-alert            Cron script: scan journal for critical events
```

### Pillar (`salt/pillar/`)

```
pillar/
├── top.sls              Pillar top file
├── network.sls          Hostname, domain, DNS servers, NTP
├── locale.sls           Timezone, system locale
├── contact.sls          Company name and security contact email
├── users.sls            User accounts, groups, SSH public keys, sudo config
├── ssh.sls              SSH port, auth settings, allowed users
├── mail.sls             Smarthost relay, root alias
├── apt.sls              Mirror, codename override
├── firewall.sls         Allowed ingress TCP ports, egress TCP/UDP ports
├── kernel.sls           Kernel flags: docker_host, perf_event_paranoid, sysrq, coredump
├── fail2ban.sls         Ban time, find time, max retries
├── logging.sls          journald rotation limits
└── secrets/
    └── server.sls.enc   SOPS-encrypted secrets (SMTP credentials, SSH keys)
```

---

## Testing with Docker

The Docker container is a plain Debian target (sshd + Python 3, no Salt installed).
salt-ssh runs from WSL, connects over SSH on port 2222, and applies states remotely.
The container boots with systemd as PID 1 (privileged mode), allowing full testing
of services, timers, and hostname.

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) and
`salt-ssh` installed in WSL.

```bash
./scripts/test.py build   # Remove container and rebuild image
./scripts/test.py shell   # Start container, open shell
./scripts/test.py ssh     # Start container, SSH into it as admin
./scripts/test.py test    # Start container, run highstate via salt-ssh
./scripts/test.py clean   # Remove container, image, and volumes
```

The container auto-starts and auto-builds if not already running.
The test command decrypts secrets before applying states, then cleans up
decrypted files automatically on exit.

---

## Firewall

The firewall is managed by `security.firewall` using **nftables** with a single `inet`
table covering both IPv4 and IPv6. All chains default to **drop** — everything must be
explicitly permitted.

Configuration is pillar-driven via `salt/pillar/firewall.sls`.

### Ingress

Only the following inbound traffic is accepted:

- **Loopback** — unrestricted
- **Established/related** — stateful tracking for existing connections
- **ICMP / ICMPv6** — operational types only: echo, destination-unreachable, time-exceeded, parameter-problem. ICMPv6 additionally includes NDP types required for IPv6 neighbour discovery (RFC 4861)
- **TCP ports** — defined in `firewall:tcp_ports` pillar (default: 22, 80, 443)
- **SSH rate limit** — new SSH connections are additionally rate-limited to 4/minute

Everything else is logged (`nftables-drop:`) and dropped.

To open additional inbound ports, add them to the pillar:

```yaml
firewall:
  tcp_ports:
    - 22
    - 80
    - 443
    - 8443   # example: additional HTTPS port
```

### Egress

The output chain is **default-drop**. Only explicitly listed destinations are allowed
outbound. This limits the damage from a compromised process — it cannot freely beacon,
exfiltrate, or download payloads.

Permitted egress, configured in `firewall:egress`:

| Protocol | Port | Purpose |
|---|---|---|
| TCP | 53 | DNS |
| TCP | 443 | APT updates, HTTPS |
| TCP | 587 | SMTP submission (STARTTLS) |
| TCP | 465 | SMTP submission (implicit TLS) |
| UDP | 53 | DNS |
| UDP | 123 | NTP |

Everything else is logged (`nftables-drop-out:`) and dropped.

To add egress for an upstream API or service:

```yaml
firewall:
  egress:
    tcp_ports:
      - 53
      - 443
      - 587
      - 465
      - 5432   # example: external PostgreSQL
```

**Limitations of port-based egress filtering:**

Port numbers are convention, not enforcement. A determined attacker can tunnel C2
traffic over port 443. Port-based egress is effective against unsophisticated malware
using default ports, accidental misconfiguration, and limiting blast radius by blocking
common reverse shell ports. It is **not** effective against HTTPS-based C2 or DNS
tunneling. AppArmor (per-process network restrictions) and auditd provide complementary
controls at the host level.

### Forward chain

Default drop. The server does not route traffic between interfaces.

### Adding a web application with an upstream service

When nginx proxies to a local backend (e.g. `localhost:8080`), that traffic travels
over loopback and is already permitted — no firewall changes needed.

If nginx proxies to an **external** upstream (e.g. an API on another host), add the
upstream port to `firewall:egress:tcp_ports`.

---

## Security Hardening

Based on [CIS Debian Linux 12 Benchmark v1.1.0](https://www.cisecurity.org/benchmark/debian_linux)
(2024-09-26) and [ANSSI BP-028](https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/).

### Implemented

**CIS Section 1 — Initial Setup:**
- 1.1.1 — Disable unused kernel modules (cramfs, hfs, jffs2, overlayfs, usb-storage, etc.)
- 1.2.1 — APT trust chain permissions (GPG keys, keyrings, sources, auth)
- 1.5.1 — ASLR enabled
- 1.5.2 — ptrace restricted (Yama)
- 1.5.3 — Core dumps disabled
- 1.7.1–1.7.4 — Login banners: issue cleared, issue.net with access notice and responsible disclosure request, MOTD managed, PAM dynamic motd suppressed

**CIS Section 2 — Services:**
- 2.2.x — Unwanted client packages removed (nis, rsh, talk, telnet, ftp, ldap-utils, strace)
- 2.4 — cron/at restricted to root

**CIS Section 3 — Network:**
- 3.2 — Unused network protocols disabled (dccp, sctp, rds, tipc)
- 3.3 — Network parameters hardened (sysctl)

**CIS Section 4 — Firewall:**
- 4.x — nftables with default-deny ingress and egress

**CIS Section 5 — Access Control:**
- 5.1 — SSH hardened (ed25519 only, restricted algorithms, forwarding disabled)
- 5.2.1–5.2.3 — sudo with pty and logfile
- 5.2.7 — su restricted to sudo group via pam_wheel
- 5.3.1–5.3.2 — PAM: faillock (3 attempts, 15-min lockout), nullok disabled
- 5.4.1 — pam_access: login restricted to pillar-defined users

**CIS Section 6 — Logging:**
- 6.1.1.2 — Journal log directory permissions (2750, root:systemd-journal)
- 6.1.1.3 — Journal rotation limits (pillar-configurable)
- 6.1.2.2 — Syslog forwarding disabled (ForwardToSyslog=no)
- 6.1.2.3 — Journal compression enabled
- 6.1.2.4 — Persistent journal storage
- rsyslog purged (journald-only logging)

**CIS Section 7 — System Maintenance:**
- 7.1.1–7.1.4 — passwd/group file permissions enforced
- 7.1.5–7.1.8 — shadow/gshadow file permissions enforced
- 7.1.9 — /etc/shells permissions enforced
- 7.1.10 — /etc/security/opasswd permissions enforced
- 7.2.1 — Unused default users removed (sync, games, lp, news, proxy, list, irc)
- 7.2.9 — Home directory permissions enforced (0750)

**ANSSI BP-028:**
- R9 — perf_event_paranoid=3, perf_cpu_time_max_percent=1, perf_event_max_sample_rate=1
- R12 — tcp_rfc1337, ip_local_port_range, accept_local, shared_media, route_localnet, arp_filter, arp_ignore, drop_gratuitous_arp
- R14 — fs.protected_fifos=2, fs.protected_regular=2

**Additional hardening:**
- APT: seccomp sandbox, HTTPS mirror, forbid unauthenticated packages, recommends/suggests disabled
- PKI: CA trust store and SSL directory permissions enforced
- Automatic security updates with needrestart
- Kernel: kptr_restrict, dmesg_restrict, BPF hardening, sysrq disabled
- Filesystem: protected hardlinks/symlinks, suid_dumpable disabled
- Hourly cron alert for critical journal events (oops, OOM, MCE, filesystem errors)
- Root-specific motd (mode 0640) with faillock quick-reference

### Authentication policy

- Users authenticate via SSH keys only — passwords are locked
- Only root retains a password (for console recovery)
- sudo is NOPASSWD for authorized users
- su is restricted to the sudo group
- `even_deny_root` intentionally off — root must remain accessible from console

### Log retention

- journald (system + security): 180 days, 1 GB cap (pillar-configurable)
- logrotate (service logs): 90 days, daily, compressed (pillar-configurable)
- fail2ban logs to journald (not file-based)

### Docker host mode

Set `kernel:docker_host: True` in `salt/pillar/kernel.sls` when the managed host
runs Docker. This enables ip_forward, allows the overlayfs module, and skips
ARP hardening options that break container networking.

### Excluded by design

- 1.1.2 — Mount options (per-server, depends on partition layout)
- 1.3 — AppArmor (see TODO.md)
- 1.4 — GRUB bootloader password (physical access scope)
- ANSSI R9 — kernel.panic_on_oops (single-instance availability risk; see TODO.md)
- 6.1.3.x — Remote logging (see TODO.md)
- 6.2 — auditd (see TODO.md)
- 7.1.11–7.1.13 — World-writable, unowned, SUID/SGID file audits (periodic; see TODO.md)
- 7.2.x — User/group integrity audits (periodic; see TODO.md)

---

## Secrets Management

Secrets are encrypted at rest using [SOPS](https://github.com/getsops/sops) with
[age](https://github.com/FiloSottile/age) as the encryption backend. This allows
secrets to be committed to the repository safely — only holders of the private age
key can decrypt them.

Encrypted files live in `salt/pillar/secrets/*.sls.enc` (committed to git). Before
salt-ssh runs, `test.py` decrypts them to `*.sls` (gitignored). After salt-ssh
finishes, decrypted files are deleted automatically.

```bash
# Edit secrets (decrypts in $EDITOR, re-encrypts on save)
scripts/sops.py edit salt/pillar/secrets/server.sls.enc

# Import a binary file (e.g. SSH key) as base64
scripts/sops.py import salt/pillar/secrets/server.sls.enc ssh.admin_ed25519 ~/.ssh/id_ed25519

# Export a base64 value back to a file
scripts/sops.py export salt/pillar/secrets/server.sls.enc ssh.admin_ed25519 /tmp/key

# Rotate data encryption keys
scripts/sops.py rotate salt/pillar/secrets/server.sls.enc
```

Secrets are available in states as regular pillar data:

```yaml
/etc/exim4/passwd.client:
  file.managed:
    - contents_pillar: secrets:mail:passwd_client
```
