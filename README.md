# server-salt

SaltStack configuration for a Debian Bookworm server, managed via salt-ssh. Tested via Docker.

---

## Directory Structure

### States (`salt/states/`)

```
states/
├── top.sls                          State top file — '*': [secure_linux]
├── secure_linux/
│   └── init.sls                     Umbrella state — static include list of all hardening states
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
│   ├── coredump.sls                 Disable core dumps
│   ├── cron.sls                     Restrict cron access
│   ├── packages.sls                 Remove insecure/unnecessary packages
│   ├── etc-passwd.sls               Auth file permissions, remove unused users
│   ├── banners.sls                  Login banners: issue.net, motd, motd.root
│   ├── pki.sls                      Keyring, CA trust store, SSL permissions
│   └── files/                       Config templates
│
├── www/                             Web services
│   └── nginx/
│       ├── init.sls                 nginx — hardened base config, catch-all vhost
│       └── files/                   nginx.conf, default-site.conf templates
│
└── monitoring/                      Logging and alerting
    ├── rsyslog.sls                  Purge rsyslog (journald-only)
    ├── journald.sls                 Harden systemd-journald (CIS 6.1)
    ├── logrotate.sls                Log rotation
    ├── alerts.sls                   Hourly journal alert cron
    └── files/                       Config templates

```

### Pillar (`salt/pillar/`)

```
pillar/
├── top.sls              Pillar top file — defaults/* for all hosts, hosts/* per group
├── defaults/            Base values applied to all hosts
│   ├── network.sls      Hostname, domain, DNS servers, NTP
│   ├── locale.sls       Timezone, system locale
│   ├── contact.sls      Company name and security contact email
│   ├── users.sls        User accounts, groups, SSH public keys, sudo config
│   ├── ssh.sls          SSH port, auth settings, allowed users
│   ├── mail.sls         Smarthost relay, root alias
│   ├── apt.sls          Codename override, unattended-upgrades schedule
│   ├── firewall.sls     Allowed ingress TCP ports, egress TCP/UDP ports
│   ├── kernel.sls       Kernel flags: docker_host, ipv6_disable, perf_event_paranoid, sysrq, coredump
│   ├── fail2ban.sls     Ban time, find time, max retries
│   └── logging.sls      journald rotation limits
├── hosts/               Per-host-group overrides (deep-merged over defaults)
│   ├── test_docker.sls
│   ├── test_hetzner.sls
│   └── test_oci.sls
└── secrets/
    └── hosts/
        ├── test_docker.sls.enc    SOPS-encrypted secrets (SMTP credentials, SSH keys)
        ├── test_hetzner.sls.enc
        └── test_oci.sls.enc
```

---

## Testing with Docker

The Docker container is a plain Debian target (sshd + Python 3, no Salt installed).
salt-ssh runs from WSL, connects over SSH on port 2222, and applies states remotely.
The container boots with systemd as PID 1 (privileged mode), allowing full testing
of services, timers, and hostname.

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) and
`salt-ssh` installed in WSL. Create `.docker.env` (gitignored):

```bash
cat > .docker.env <<EOF
DOCKER_SSH_PORT=2222
ADMIN_SSH_KEY=~/.ssh/admin_ed25519
EOF
```

```bash
./scripts/test-docker.py build   # Remove container and rebuild image
./scripts/test-docker.py shell   # Start container, open shell
./scripts/test-docker.py ssh     # Start container, SSH into it as admin
./scripts/test-docker.py check   # Start container, apply single state (fast smoke test)
./scripts/test-docker.py test    # Start container, run highstate via salt-ssh
./scripts/test-docker.py clean   # Remove container, image, and volumes
```

The container auto-starts and auto-builds if not already running. Each test runner
writes `salt/roster` dynamically, decrypts secrets, runs the highstate, and cleans
up both on exit.

---

## Testing with a VM (Hetzner or OCI)

For higher-fidelity testing — real kernel, real sysctl namespace, real `/boot`,
real systemd — use a cloud VM. Cost is negligible (~€0.006/hour on Hetzner; free
tier available on OCI).

Docker is fast for iteration. VM testing is for final validation, especially for
kernel hardening states (`security.sysctl`, `security.boot`).

### Hetzner

```bash
# One-time: install hcloud CLI
sudo apt-get install hcloud-cli

# Create .hetzner.env (gitignored):
cat > .hetzner.env <<EOF
HCLOUD_TOKEN=your-api-token
HETZNER_SERVER_TYPE=cx22
HETZNER_LOCATION=fsn1
ADMIN_SSH_KEY=~/.ssh/admin_ed25519
EOF

# Optional: register the admin SSH key in your Hetzner project
hcloud ssh-key create --name admin --public-key-from-file ~/.ssh/admin_ed25519.pub
```

```bash
./scripts/test-hetzner.py create   # Create VM, wait for SSH (30–60s)
./scripts/test-hetzner.py check    # Apply single state (fast smoke test, creates VM if needed)
./scripts/test-hetzner.py test     # Run highstate (creates VM if needed)
./scripts/test-hetzner.py ssh      # SSH into VM as admin
./scripts/test-hetzner.py delete   # Destroy VM
./scripts/test-hetzner.py ip       # Print current VM IP
```

### Oracle OCI

```bash
# One-time: install OCI CLI and configure ~/.oci/config
# Then create .oci.env (gitignored):
cat > .oci.env <<EOF
OCI_COMPARTMENT_OCID=ocid1.tenancy.oc1...<your-ocid>
OCI_IMAGE_OCID=ocid1.image.oc1...<your-image-ocid>
OCI_SUBNET_OCID=ocid1.subnet.oc1...<your-subnet-ocid>
OCI_BUCKET_NAME=debian-images
OCI_SHAPE=VM.Standard.E2.1.Micro
ADMIN_SSH_KEY=~/.ssh/admin_ed25519
EOF
```

```bash
./scripts/test-oci.py auth           # Verify OCI credentials
./scripts/test-oci.py upload-image   # Import Debian genericcloud image (once)
./scripts/test-oci.py create         # Create VM, wait for SSH
./scripts/test-oci.py check          # Apply single state (fast smoke test, creates VM if needed)
./scripts/test-oci.py test           # Run highstate (creates VM if needed)
./scripts/test-oci.py ssh            # SSH into VM as admin
./scripts/test-oci.py delete         # Terminate VM
```

Both runners write a temporary roster with the VM's IP, decrypt secrets, run the
highstate, and clean up on exit. The VM is **not** destroyed automatically — run
`delete` when done.

**Firewall note:** `security.firewall` applies nftables with live egress default-drop.
On a VM this is immediately enforced. If locked out, use the provider's web console.

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

Encrypted files live in `salt/pillar/secrets/hosts/<group>.sls.enc` (committed to git).
Before salt-ssh runs, the test runner decrypts them to `*.sls` (gitignored). After
salt-ssh finishes, decrypted files are deleted automatically.

```bash
# Edit secrets (decrypts in $EDITOR, re-encrypts on save)
scripts/sops.py edit salt/pillar/secrets/hosts/test_docker.sls.enc

# Import a binary file (e.g. SSH key) as base64
scripts/sops.py import salt/pillar/secrets/hosts/test_docker.sls.enc ssh.admin_ed25519 ~/.ssh/id_ed25519

# Export a base64 value back to a file
scripts/sops.py export salt/pillar/secrets/hosts/test_docker.sls.enc ssh.admin_ed25519 /tmp/key

# Rotate data encryption keys
scripts/sops.py rotate salt/pillar/secrets/hosts/test_docker.sls.enc
```

Secrets are available in states as regular pillar data:

```yaml
/etc/exim4/passwd.client:
  file.managed:
    - contents_pillar: secrets:mail:passwd_client
```
