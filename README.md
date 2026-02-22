# server-salt

SaltStack configuration for a some what secure Debian Bookworm server, managed via salt-ssh.

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
real systemd — use a cloud VM.

Docker is fast for iteration. VM testing is for final validation, especially for kernel hardening states (`security.sysctl`, `security.boot`).

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

nftables, single `inet` table, all chains default-drop. Pillar: `defaults/firewall.sls`.

- **Ingress** — loopback unrestricted; established/related; TCP ports from `firewall:tcp_ports` (default: 22, 80, 443); unmatched logged and dropped
- **Egress** — TCP 53/443/465/587, UDP 53/123; loopback unrestricted; unmatched logged and dropped
- **ICMP** — echo, destination-unreachable, time-exceeded, parameter-problem
- **ICMPv6** — same operational types plus NDP (RFC 4861 neighbour discovery)
- **Rate limit** — SSH new connections limited to 4/minute
- **Forward** — default drop

---

## Security Hardening

Based on [CIS Debian Linux 13 Benchmark v1.0.0](https://www.cisecurity.org/benchmark/debian_linux)
and [ANSSI BP-028](https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/).

See [compliance.md](compliance.md) for a full control-by-control status.

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
