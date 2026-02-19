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
│   ├── fstab.sls                    Mount hardening (nosuid,nodev,noexec on /boot)
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
│   ├── bash.sls                     Bashrc, umask, /etc/shells hardening
│   ├── vim.sls                      Vim config, set as default editor
│   ├── git.sls                      Git installation
│   ├── packages.sls                 Common utility packages
│   └── files/                       Config templates (bash.bashrc, vimrc.local, umask.sh)
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
│   ├── sysctl.sls                   Kernel hardening (sysctl.d + modprobe blacklist)
│   ├── boot.sls                     /boot permissions (CIS 1.4.2, ANSSI R29)
│   ├── pam.sls                      PAM: faillock, access control, umask, lastlog, yescrypt
│   ├── etc-passwd.sls               Auth file permissions, remove unused users
│   ├── banners.sls                  Login banners: issue.net, motd, motd.root
│   ├── pki.sls                      Keyring, CA trust store, SSL permissions
│   └── files/                       nftables.conf, faillock.conf, access.conf,
│                                    pam-*, 99-hardening.conf, modprobe-blacklist.conf,
│                                    motd, motd.root, issue.net
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
├── kernel.sls           Kernel flags: docker_host, ipv6_disable, perf_event_paranoid, sysrq, coredump
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

---

### Secrets Management

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
