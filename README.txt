# server-salt

SaltStack configuration for a Debian Linux web server.

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
│   ├── firewall.sls                 nftables — default deny, allow SSH/HTTP(S)
│   ├── fail2ban.sls                 Brute-force protection for SSH
│   ├── sysctl.sls                   Kernel hardening (sysctl.d)
│   ├── etc-passwd.sls               Auth file permissions, remove unused users (CIS 7.1, 7.2)
│   ├── banners.sls                  Login banners: empty issue/issue.net, MOTD (CIS 1.7)
│   ├── pki.sls                      Keyring, CA trust store, SSL permissions
│   └── files/                       nftables.conf, jail.local, 99-hardening.conf, motd
│
└── monitoring/                      Logging and system info
    ├── rsyslog.sls                  Purge rsyslog (journald-only)
    ├── journald.sls                 Harden systemd-journald (CIS 6.1)
    ├── logrotate.sls                Log rotation
    └── files/
        ├── 99-journald.conf         journald hardening config (Jinja)
        └── logrotate.conf           logrotate base config
```

### Pillar (`salt/pillar/`)

```
pillar/
├── top.sls              Pillar top file
├── network.sls          Hostname, domain, DNS servers, NTP
├── locale.sls           Timezone, system locale
├── users.sls            User accounts, groups, SSH public keys, sudo config
├── ssh.sls              SSH port, auth settings, allowed users
├── mail.sls             Smarthost relay, root alias
├── apt.sls              Mirror, codename override
├── firewall.sls         Allowed TCP ports
├── fail2ban.sls         Ban time, find time, max retries
├── logging.sls          journald rotation limits
└── secrets/
    └── server.sls.enc   SOPS-encrypted secrets (SMTP credentials, SSH keys)
```

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

## Security Hardening

Based on [CIS Debian Linux 12 Benchmark v1.1.0](https://www.cisecurity.org/benchmark/debian_linux) (2024-09-26).

### Implemented CIS Sections

**Section 1 — Initial Setup:**
- 1.1.1 — Disable unused kernel modules (cramfs, hfs, jffs2, overlayfs, usb-storage, etc.)
- 1.2.1 — APT trust chain permissions (GPG keys, keyrings, sources, auth)
- 1.5.1 — ASLR enabled
- 1.5.2 — ptrace restricted
- 1.5.3 — Core dumps disabled
- 1.7.1–1.7.3 — Login banners configured (issue, issue.net emptied, MOTD managed)

**Section 2 — Services:**
- 2.2.x — Unwanted client packages removed (nis, rsh, talk, telnet, ftp, ldap-utils)
- 2.4 — cron/at restricted to root

**Section 3 — Network:**
- 3.2 — Unused network protocols disabled (dccp, sctp, rds, tipc)
- 3.3 — Network parameters hardened (sysctl)

**Section 4 — Firewall:**
- 4.x — nftables with default-deny policy

**Section 5 — Access Control:**
- 5.1 — SSH hardened (ed25519 only, restricted algorithms, forwarding disabled, host key permissions)
- 5.2.1-5.2.3 — sudo with pty and logfile
- 5.2.7 — su restricted to sudo group via pam_wheel

**Section 6 — Logging:**
- 6.1.1.2 — Journal log directory permissions (2750, root:systemd-journal)
- 6.1.1.3 — Journal rotation limits (pillar-configurable)
- 6.1.2.2 — Syslog forwarding disabled (ForwardToSyslog=no)
- 6.1.2.3 — Journal compression enabled
- 6.1.2.4 — Persistent journal storage
- rsyslog purged (journald-only logging)

**Section 7 — System Maintenance:**
- 7.1.1–7.1.4 — passwd/group file permissions enforced (0644, root:root)
- 7.1.5–7.1.8 — shadow/gshadow file permissions enforced (0640, root:shadow)
- 7.1.9 — /etc/shells permissions enforced (0644, root:root)
- 7.1.10 — /etc/security/opasswd permissions enforced (0600, root:root)
- 7.2.1 — Unused default users removed (sync, games, lp, news, proxy, list, irc)
- 7.2.9 — Home directory permissions enforced (0750)

**Authentication policy:**
- Users authenticate via SSH keys only — passwords are locked
- Only root retains a password (for console recovery)
- sudo is NOPASSWD for authorized users
- su is restricted to the sudo group

**Log retention policy:**
- journald (system + security): 180 days, 1GB cap (pillar-configurable)
- logrotate (service logs): 90 days, daily, compressed (pillar-configurable)
- fail2ban logs to journald (not file-based)
- Package-managed logs (apt, dpkg, exim4) use their own logrotate.d configs

**Additional hardening (beyond CIS):**
- APT: seccomp sandbox, HTTPS mirror, forbid unauthenticated packages, recommends/suggests disabled
- PKI: CA trust store and SSL directory permissions enforced, keyring permissions enforced
- Automatic security updates with needrestart and scheduled reboot
- Kernel: kptr_restrict, dmesg_restrict, BPF hardening, sysrq disabled
- Filesystem: protected hardlinks/symlinks, suid_dumpable disabled

### Excluded (by design)
- 1.1.2 — Mount options (per-server, depends on partition/LUKS layout)
- 1.3 — AppArmor (operational complexity)
- 1.4 — GRUB bootloader password (physical access scope)
- 6.1.3.x — Remote logging (see TODO.md)
- 6.2 — auditd (see TODO.md)
- 7.1.11–7.1.13 — World-writable, unowned, SUID/SGID file audits (periodic, see TODO.md)
- 7.2.1–7.2.8 — User/group integrity audits (periodic, see TODO.md)

## Secrets Management

Secrets are encrypted at rest using [SOPS](https://github.com/getsops/sops) with
[age](https://github.com/FiloSottile/age) as the encryption backend. This allows
secrets to be committed to the repository safely — only holders of the private age
key can decrypt them.

### How it works

1. Encrypted files live in `salt/pillar/secrets/*.sls.enc` (committed to git)
2. Before salt-ssh runs, `test.py` decrypts them to `*.sls` (gitignored)
3. salt-ssh reads the decrypted pillar files and sends values to the target
4. After salt-ssh finishes, decrypted files are deleted automatically (`trap EXIT`)

The decrypted `.sls` files never persist on disk beyond the salt-ssh run.

### Common tasks

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

### Accessing secrets in Salt states

Secrets are available as regular pillar data under the `secrets` key:

```yaml
/etc/exim4/passwd.client:
  file.managed:
    - contents_pillar: secrets:mail:passwd_client
```

### Adding a new secret

1. Run `scripts/sops.py edit salt/pillar/secrets/server.sls.enc`
2. Add the new key/value under the `secrets:` tree
3. Save and quit — SOPS re-encrypts automatically
4. Reference it in states via `contents_pillar: secrets:path:to:key`
