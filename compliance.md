# Compliance

This document tracks compliance with the **CIS Debian Linux 13 Benchmark v1.0.0** and the
**ANSSI-BP-028 EN v2.0 — Minimal level** recommendations.

---

## Security Goals

This server configuration targets a **balanced security posture**: strong by default, without
sacrificing operational usability or maintainability. Its a single webserver, no rocket science, I hope.

**Legend**

| Mark | Meaning |
|------|---------|
| Y | Implemented and enforced by Salt states |
| N | Deliberately not implemented (rationale documented) |
| O | Open — not yet implemented or decision pending |

---

## CIS Debian Linux 13 Benchmark v1.0.0

### 1 Initial Setup

#### 1.1 Filesystem

##### 1.1.1 Kernel Modules

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.1.1.1 | cramfs kernel module not available | Y | Blacklisted in `/etc/modprobe.d/blacklist-cis.conf` |
| 1.1.1.2 | freevxfs kernel module not available | Y | Blacklisted |
| 1.1.1.3 | hfs kernel module not available | Y | Blacklisted |
| 1.1.1.4 | hfsplus kernel module not available | Y | Blacklisted |
| 1.1.1.5 | jffs2 kernel module not available | Y | Blacklisted |
| 1.1.1.6 | overlay kernel module not available | Y | Blacklisted on non-Docker hosts; conditionally allowed on docker_host |
| 1.1.1.7 | squashfs kernel module not available | Y | Blacklisted |
| 1.1.1.8 | udf kernel module not available | Y | Blacklisted |
| 1.1.1.9 | firewire-core kernel module not available | O | Not yet blacklisted; server hardware has no FireWire |
| 1.1.1.10 | usb-storage kernel module not available | Y | Blacklisted |
| 1.1.1.11 | Unused filesystems kernel modules not available | O | Manual review pending; covered partially by explicit blacklist |

##### 1.1.2 Filesystem Partitions

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.1.2.1.1 | /tmp is tmpfs or separate partition | O | Partition layout defined at provisioning; not managed by Salt |
| 1.1.2.1.2 | nodev on /tmp | O | Partition layout managed at provisioning time |
| 1.1.2.1.3 | nosuid on /tmp | O | Partition layout managed at provisioning time |
| 1.1.2.1.4 | noexec on /tmp | O | Partition layout managed at provisioning time |
| 1.1.2.2.1 | /dev/shm is tmpfs or separate partition | O | Default tmpfs; mount options not explicitly enforced |
| 1.1.2.2.2 | nodev on /dev/shm | O | Not enforced via Salt |
| 1.1.2.2.3 | nosuid on /dev/shm | O | Not enforced via Salt |
| 1.1.2.2.4 | noexec on /dev/shm | O | Not enforced via Salt |
| 1.1.2.3.1 | Separate partition for /home | O | Partition layout defined at provisioning |
| 1.1.2.3.2 | nodev on /home | O | Not enforced via Salt |
| 1.1.2.3.3 | nosuid on /home | O | Not enforced via Salt |
| 1.1.2.4.1 | Separate partition for /var | O | Partition layout defined at provisioning |
| 1.1.2.4.2 | nodev on /var | O | Not enforced via Salt |
| 1.1.2.4.3 | nosuid on /var | O | Not enforced via Salt |
| 1.1.2.5.1 | Separate partition for /var/tmp | O | Partition layout defined at provisioning |
| 1.1.2.5.2 | nodev on /var/tmp | O | Not enforced via Salt |
| 1.1.2.5.3 | nosuid on /var/tmp | O | Not enforced via Salt |
| 1.1.2.5.4 | noexec on /var/tmp | O | Not enforced via Salt |
| 1.1.2.6.1 | Separate partition for /var/log | O | Partition layout defined at provisioning |
| 1.1.2.6.2 | nodev on /var/log | O | Not enforced via Salt |
| 1.1.2.6.3 | nosuid on /var/log | O | Not enforced via Salt |
| 1.1.2.6.4 | noexec on /var/log | O | Not enforced via Salt |
| 1.1.2.7.1 | Separate partition for /var/log/audit | O | Partition layout defined at provisioning |
| 1.1.2.7.2 | nodev on /var/log/audit | O | Not enforced via Salt |
| 1.1.2.7.3 | nosuid on /var/log/audit | O | Not enforced via Salt |
| 1.1.2.7.4 | noexec on /var/log/audit | O | Not enforced via Salt |

#### 1.2 Package Management

##### 1.2.1 Package Repositories

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.2.1.1 | sources use Signed-By option | Y | DEB822 `.sources` format enforced; Signed-By included |
| 1.2.1.2 | Weak dependencies configured | Y | `APT::Install-Recommends "false"` and `APT::Install-Suggests "false"` |
| 1.2.1.3 | Access to GPG key files configured | Y | `/etc/apt/trusted.gpg.d` enforced root:root 0644 |
| 1.2.1.4 | Access to /etc/apt/trusted.gpg.d configured | Y | Managed by `apt/init.sls` |
| 1.2.1.5 | Access to /etc/apt/auth.conf.d configured | Y | Directory 0755, files 0640 |
| 1.2.1.6 | Access to files in /etc/apt/auth.conf.d configured | Y | Enforced via Salt file.directory recurse |
| 1.2.1.7 | Access to /usr/share/keyrings configured | Y | root:root 0755, files 0644 via `security/pki.sls` |
| 1.2.1.8 | Access to /etc/apt/sources.list.d configured | Y | root:root 0755 |
| 1.2.1.9 | Access to files in /etc/apt/sources.list.d configured | Y | Files 0644 enforced |

##### 1.2.2 Package Updates

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.2.2.1 | Updates, patches, and security software installed | Y | `unattended-upgrades` with daily security updates; `needrestart` for service restarts |

#### 1.3 Mandatory Access Control

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.3.1.1 | AppArmor packages installed | Y | Installed by default on Debian; verified present |
| 1.3.1.2 | AppArmor is enabled | Y | Enabled in Debian kernel and initramfs by default |
| 1.3.1.3 | All AppArmor profiles are enforcing | O | Default distribution profiles present; not actively extended or audited |
| 1.3.1.4 | apparmor_restrict_unprivileged_unconfined enabled | O | Kernel parameter not explicitly set |

#### 1.4 Bootloader

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.4.1 | Bootloader password is set | N | Physical console access is organisationally controlled; no remote boot access; password would break unattended reboots without a IPMI/KVM setup |
| 1.4.2 | Access to bootloader config is configured | Y | `/boot/grub/grub.cfg` root:root 0600; `/boot` dir 0700 via `security/boot.sls` |

#### 1.5 Additional Process Hardening

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.5.1 | fs.protected_hardlinks configured | Y | Set to 1 in `99-hardening.conf` |
| 1.5.2 | fs.protected_symlinks configured | Y | Set to 1 in `99-hardening.conf` |
| 1.5.3 | kernel.yama.ptrace_scope configured | Y | Set to 1 in `99-hardening.conf` |
| 1.5.4 | fs.suid_dumpable configured | Y | Set to 0 in `99-hardening.conf` |
| 1.5.5 | kernel.dmesg_restrict configured | Y | Set to 1 in `99-hardening.conf` |
| 1.5.6 | prelink not installed | Y | Not installed; not in any package list |
| 1.5.7 | Automatic Error Reporting configured | Y | apport not installed; crash reporting disabled |
| 1.5.8 | kernel.kptr_restrict configured | Y | Set to 2 in `99-hardening.conf` |
| 1.5.9 | kernel.randomize_va_space configured | Y | Set to 2 in `99-hardening.conf` |
| 1.5.10 | kernel.yama.ptrace_scope configured (duplicate) | Y | See 1.5.3 |
| 1.5.11 | Core file size configured | Y | `* hard core 0` in `/etc/security/limits.d/99-coredump.conf` |
| 1.5.12 | systemd-coredump ProcessSizeMax configured | Y | `ProcessSizeMax=0` in coredump drop-in |
| 1.5.13 | systemd-coredump Storage configured | Y | `Storage=none` in coredump drop-in |

#### 1.6 Command Line Warning Banners

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.6.1 | /etc/motd is configured | Y | Managed by `security/banners.sls` with system info and legal notice |
| 1.6.2 | /etc/issue is configured | Y | Set to empty (no banner on local console; physical access controlled) |
| 1.6.3 | /etc/issue.net is configured | Y | SSH banner with legal warning |
| 1.6.4 | Access to /etc/motd is configured | Y | root:root 0644 |
| 1.6.5 | Access to /etc/issue is configured | Y | root:root 0644 |
| 1.6.6 | Access to /etc/issue.net is configured | Y | root:root 0644 |

#### 1.7 GNOME Display Manager

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 1.7.1 | GDM is removed | Y | gdm3, xserver-xorg, task-gnome-desktop purged via `security/packages.sls` |
| 1.7.2 | GDM login banner configured | N | No GDM — not applicable |
| 1.7.3 | GDM disable-user-list enabled | N | No GDM — not applicable |
| 1.7.4 | GDM screen locks when user is idle | N | No GDM — not applicable |
| 1.7.5 | GDM screen locks cannot be overridden | N | No GDM — not applicable |
| 1.7.6 | GDM automatic mounting of removable media disabled | N | No GDM — not applicable |
| 1.7.7 | GDM disabling auto-mount is not overridden | N | No GDM — not applicable |
| 1.7.8 | GDM autorun-never is enabled | N | No GDM — not applicable |
| 1.7.9 | GDM autorun-never is not overridden | N | No GDM — not applicable |
| 1.7.10 | XDMCP is not enabled | N | No GDM — not applicable |
| 1.7.11 | Xwayland is configured | N | No GDM — not applicable |

---

### 2 Services

#### 2.1 Server Services

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 2.1.1 | autofs services not in use | Y | Not installed; nftables blocks unexpected traffic |
| 2.1.2 | avahi daemon not in use | Y | Not installed |
| 2.1.3 | dhcp server not in use | Y | Not installed |
| 2.1.4 | dns server not in use | Y | Not installed |
| 2.1.5 | dnsmasq not in use | Y | Not installed |
| 2.1.6 | ftp server not in use | Y | Not installed |
| 2.1.7 | ldap server not in use | Y | Not installed |
| 2.1.8 | message access server not in use | Y | Not installed (no IMAP/POP3) |
| 2.1.9 | network file system not in use | Y | Not installed |
| 2.1.10 | nis server not in use | Y | Not installed |
| 2.1.11 | print server not in use | Y | Not installed |
| 2.1.12 | rpcbind not in use | Y | Not installed |
| 2.1.13 | rsync not in use | Y | Not installed |
| 2.1.14 | samba not in use | Y | Not installed |
| 2.1.15 | snmp not in use | Y | Not installed |
| 2.1.16 | telnet-server not in use | Y | Not installed |
| 2.1.17 | tftp server not in use | Y | Not installed |
| 2.1.18 | web proxy not in use | Y | Not installed |
| 2.1.19 | web server not in use | O | May be installed for specific deployments; blocked at firewall until explicitly opened |
| 2.1.20 | xinetd not in use | Y | Not installed |
| 2.1.21 | X window server not in use | Y | Not installed |
| 2.1.22 | MTA configured for local-only mode | Y | exim4-daemon-light configured for local delivery and smarthost relay only |
| 2.1.23 | Only approved services listening on network | Y | nftables default-deny ingress; only SSH port open |

#### 2.2 Client Services

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 2.2.1 | nis client not installed | Y | Purged by `security/packages.sls` |
| 2.2.2 | rsh client not installed | Y | Purged |
| 2.2.3 | talk client not installed | Y | Purged |
| 2.2.4 | telnet client not installed | Y | Purged |
| 2.2.5 | ldap client not installed | Y | Purged |
| 2.2.6 | ftp client not installed | Y | Purged |

#### 2.3 Time Synchronization

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 2.3.1.1 | Single time synchronization daemon in use | Y | systemd-timesyncd only; no chrony or ntpd |
| 2.3.2.1 | systemd-timesyncd configured with authorized timeserver | Y | NTP servers configured via pillar in `timesyncd.conf` |
| 2.3.2.2 | systemd-timesyncd is enabled and running | Y | Enabled and running via `base/ntp.sls` |

#### 2.4 Job Schedulers

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 2.4.1.1 | cron daemon enabled and active | Y | cron installed and running |
| 2.4.1.2 | Access to /etc/crontab configured | Y | 0600 root:root |
| 2.4.1.3 | Access to /etc/cron.hourly configured | Y | 0700 |
| 2.4.1.4 | Access to /etc/cron.daily configured | Y | 0700 |
| 2.4.1.5 | Access to /etc/cron.weekly configured | Y | 0700 |
| 2.4.1.6 | Access to /etc/cron.monthly configured | Y | 0700 |
| 2.4.1.7 | Access to /etc/cron.yearly configured | Y | 0700 if exists; not created if missing |
| 2.4.1.8 | Access to /etc/cron.d configured | Y | 0700 |
| 2.4.1.9 | Access to crontab is configured | Y | `/etc/cron.allow` contains root only; `/etc/cron.deny` absent |
| 2.4.2.1 | Access to at is configured | Y | `/etc/at.allow` contains root only; `/etc/at.deny` absent |

---

### 3 Network

#### 3.1 Network Devices

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 3.1.1 | IPv6 disabled | Y | Disabled via net.ipv6.conf.all.disable_ipv6; pillar kernel:ipv6_disable controls this |
| 3.1.2 | Wireless interfaces not available | Y | Server hardware; no wireless; cfg80211/mac80211 blacklisted via modprobe |
| 3.1.3 | Bluetooth not in use | Y | Package purged; bluetooth/btusb blacklisted via modprobe |

#### 3.2 Network Kernel Modules

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 3.2.1 | atm kernel module not available | Y | Blacklisted in `modprobe-blacklist.conf` |
| 3.2.2 | can kernel module not available | Y | Blacklisted in `modprobe-blacklist.conf` |
| 3.2.3 | dccp kernel module not available | Y | Blacklisted in `modprobe-blacklist.conf` |
| 3.2.4 | rds kernel module not available | Y | Blacklisted |
| 3.2.5 | sctp kernel module not available | Y | Blacklisted |
| 3.2.6 | tipc kernel module not available | Y | Blacklisted |

#### 3.3 Network Kernel Parameters

##### 3.3.1 IPv4 Parameters

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 3.3.1.1 | net.ipv4.ip_forward configured | Y | 0 (non-Docker) or 1 (docker_host) via sysctl |
| 3.3.1.2 | net.ipv4.conf.all.forwarding configured | Y | Matches ip_forward setting |
| 3.3.1.3 | net.ipv4.conf.default.forwarding configured | O | Not explicitly set; follows kernel default |
| 3.3.1.4 | net.ipv4.conf.all.send_redirects configured | Y | Set to 0 |
| 3.3.1.5 | net.ipv4.conf.default.send_redirects configured | Y | Set to 0 |
| 3.3.1.6 | net.ipv4.icmp_ignore_bogus_error_responses configured | Y | Set to 1 |
| 3.3.1.7 | net.ipv4.icmp_echo_ignore_broadcasts configured | Y | Set to 1 |
| 3.3.1.8 | net.ipv4.conf.all.accept_redirects configured | Y | Set to 0 |
| 3.3.1.9 | net.ipv4.conf.default.accept_redirects configured | Y | Set to 0 |
| 3.3.1.10 | net.ipv4.conf.all.secure_redirects configured | Y | Set to 0 |
| 3.3.1.11 | net.ipv4.conf.default.secure_redirects configured | Y | Set to 0 |
| 3.3.1.12 | net.ipv4.conf.all.rp_filter configured | Y | Set to 1 |
| 3.3.1.13 | net.ipv4.conf.default.rp_filter configured | Y | Set to 1 |
| 3.3.1.14 | net.ipv4.conf.all.accept_source_route configured | Y | Set to 0 |
| 3.3.1.15 | net.ipv4.conf.default.accept_source_route configured | Y | Set to 0 |
| 3.3.1.16 | net.ipv4.conf.all.log_martians configured | Y | Set to 1 |
| 3.3.1.17 | net.ipv4.conf.default.log_martians configured | Y | Set to 1 |
| 3.3.1.18 | net.ipv4.tcp_syncookies configured | Y | Set to 1 |

##### 3.3.2 IPv6 Parameters

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 3.3.2.1 | net.ipv6.conf.all.forwarding configured | Y | Set to 0 (unless docker_host) |
| 3.3.2.2 | net.ipv6.conf.default.forwarding configured | O | Not explicitly set |
| 3.3.2.3 | net.ipv6.conf.all.accept_redirects configured | Y | Set to 0 |
| 3.3.2.4 | net.ipv6.conf.default.accept_redirects configured | Y | Set to 0 |
| 3.3.2.5 | net.ipv6.conf.all.accept_source_route configured | Y | Set to 0 |
| 3.3.2.6 | net.ipv6.conf.default.accept_source_route configured | O | Not explicitly set |
| 3.3.2.7 | net.ipv6.conf.all.accept_ra configured | O | Not configured; relevant if IPv6 is used |
| 3.3.2.8 | net.ipv6.conf.default.accept_ra configured | O | Not configured |

---

### 4 Host Based Firewall

> **Note:** CIS recommends ufw. This configuration uses **nftables** instead, which provides equivalent or stronger packet filtering. The functional requirements (default deny, controlled ingress/egress) are fully met.

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 4.1.1 | ufw is installed | N | nftables used instead; equivalent protection achieved |
| 4.1.2 | ufw service is configured | N | nftables service managed by `security/firewall.sls` |
| 4.1.3 | ufw incoming default deny | Y | nftables default policy: drop on input chain |
| 4.1.4 | ufw outgoing default configured | Y | nftables outgoing policy configured |
| 4.1.5 | ufw routed default configured | Y | nftables forward policy: drop |

---

### 5 Access Control

#### 5.1 SSH Server

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 5.1.1 | Access to /etc/ssh/sshd_config configured | Y | Mode 0600 root:root |
| 5.1.2 | Access to SSH private host key files configured | Y | Mode 0600 |
| 5.1.3 | Access to SSH public host key files configured | Y | Mode 0644 |
| 5.1.4 | sshd access configured | Y | AllowUsers set via pillar |
| 5.1.5 | sshd Banner configured | Y | Banner points to /etc/issue.net |
| 5.1.6 | sshd Ciphers configured | Y | chacha20-poly1305, aes256-gcm, aes128-gcm only |
| 5.1.7 | sshd ClientAliveInterval and CountMax configured | Y | Interval 300s, CountMax 2 |
| 5.1.8 | sshd DisableForwarding enabled | Y | DisableForwarding yes |
| 5.1.9 | sshd GSSAPIAuthentication disabled | Y | Not enabled; OpenSSH default is no |
| 5.1.10 | sshd HostbasedAuthentication disabled | Y | Not enabled; OpenSSH default is no |
| 5.1.11 | sshd IgnoreRhosts enabled | Y | Not set (default yes in modern OpenSSH) |
| 5.1.12 | sshd KexAlgorithms configured | Y | curve25519-sha256 variants only |
| 5.1.13 | sshd post-quantum key exchange algorithms configured | O | MLKEM not yet configured; requires OpenSSH 9.9+ |
| 5.1.14 | sshd LoginGraceTime configured | Y | Set to 30s |
| 5.1.15 | sshd LogLevel configured | Y | VERBOSE |
| 5.1.16 | sshd MACs configured | Y | hmac-sha2-512-etm, hmac-sha2-256-etm only |
| 5.1.17 | sshd MaxAuthTries configured | Y | Configured via pillar (default 3) |
| 5.1.18 | sshd MaxSessions configured | Y | Configured via pillar (default 3) |
| 5.1.19 | sshd MaxStartups configured | O | Not explicitly set; uses OpenSSH default (10:30:100) |
| 5.1.20 | sshd PermitEmptyPasswords disabled | Y | PermitEmptyPasswords no |
| 5.1.21 | sshd PermitRootLogin disabled | Y | PermitRootLogin no (configurable via pillar) |
| 5.1.22 | sshd PermitUserEnvironment disabled | Y | Not set; OpenSSH default is no |
| 5.1.23 | sshd UsePAM enabled | Y | UsePAM yes |

#### 5.2 Privilege Escalation (sudo)

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 5.2.1 | sudo is installed | Y | Installed by `access/sudo.sls` |
| 5.2.2 | sudo commands use pty | Y | `Defaults use_pty` in `/etc/sudoers.d/99-cis` |
| 5.2.3 | sudo log file exists | Y | `Defaults logfile="/var/log/sudo.log"` |
| 5.2.4 | Users must provide password for escalation | N | NOPASSWD used per project policy (SSH-key-only auth; sudo with password would require setting passwords, which contradicts authentication policy) |
| 5.2.5 | Re-authentication for privilege escalation not disabled globally | O | timestamp_timeout uses default; not explicitly hardened |
| 5.2.6 | sudo timestamp_timeout configured | O | Not explicitly set |
| 5.2.7 | Access to su restricted | Y | pam_wheel enforces sudo group membership for su |

#### 5.3 Pluggable Authentication Modules (PAM)

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 5.3.1.1 | Latest pam installed | Y | Managed by unattended-upgrades |
| 5.3.1.2 | Latest libpam-modules installed | Y | Managed by unattended-upgrades |
| 5.3.1.3 | Latest libpam-pwquality installed | N | Not explicitly installed; not needed (SSH-key-only, no user passwords) |
| 5.3.2.1 | pam_unix module enabled | Y | Present in common-auth |
| 5.3.2.2 | pam_faillock module enabled | Y | Present in common-auth; configured in faillock.conf |
| 5.3.2.3 | pam_pwquality module enabled | N | Users have no passwords (locked); SSH key only. Password quality enforcement is irrelevant for user accounts |
| 5.3.2.4 | pam_pwhistory module enabled | N | Same rationale — no user passwords to track history for |
| 5.3.3.1.1 | Password failed attempts lockout configured | Y | deny=3, fail_interval=900 in faillock.conf |
| 5.3.3.1.2 | Password unlock time configured | Y | unlock_time=900 in faillock.conf |
| 5.3.3.1.3 | Password failed attempts lockout includes root | N | Root login disabled via SSH (PermitRootLogin no); root not locked out to preserve console recovery |
| 5.3.3.2.1 | Password number of changed characters configured | N | No user passwords; SSH key only |
| 5.3.3.2.2 | Password length configured | N | No user passwords |
| 5.3.3.2.3 | Password complexity configured | N | No user passwords |
| 5.3.3.2.4 | Password same consecutive characters configured | N | No user passwords |
| 5.3.3.2.5 | Password maximum sequential characters configured | N | No user passwords |
| 5.3.3.2.6 | Password dictionary check enabled | N | No user passwords |
| 5.3.3.2.7 | Password quality checking enforced | N | No user passwords |
| 5.3.3.2.8 | Password quality enforced for root | N | Root has a password (for console recovery); root password quality not enforced via PAM |
| 5.3.3.3.1 | Password history remember configured | N | No user passwords |
| 5.3.3.3.2 | Password history enforced for root | N | Root has a password; history not enforced |
| 5.3.3.3.3 | pam_pwhistory includes use_authtok | N | No user passwords |
| 5.3.3.4.1 | pam_unix does not include nullok | Y | nullok explicitly removed from common-auth |
| 5.3.3.4.2 | pam_unix does not include remember | N | Not configured |
| 5.3.3.4.3 | pam_unix includes strong password hashing algorithm | Y | yescrypt configured in `common-password` via `security/pam.sls` |
| 5.3.3.4.4 | pam_unix includes use_authtok | O | Not configured |

#### 5.4 User Accounts and Environment

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 5.4.1.1 | Password expiration configured | N | Users have no passwords; accounts locked from creation |
| 5.4.1.2 | Minimum password days configured | N | No user passwords |
| 5.4.1.3 | Password expiration warning days configured | N | No user passwords |
| 5.4.1.4 | Strong password hashing algorithm configured | Y | /etc/login.defs default; not explicitly enforced for root |
| 5.4.1.5 | Inactive password lock configured | N | Accounts locked immediately at creation |
| 5.4.1.6 | All users last password change in the past | Y | N/A — all user accounts have locked passwords; no future-dated changes |
| 5.4.2.1 | Root is the only UID 0 account | Y | Enforced; Salt removes spurious default accounts |
| 5.4.2.2 | Root is the only GID 0 account | Y | Enforced |
| 5.4.2.3 | Group root is the only GID 0 group | Y | Enforced |
| 5.4.2.4 | Root account access is controlled | Y | Direct root login disabled via SSH; su restricted to sudo group |
| 5.4.2.5 | Root path integrity | O | Not explicitly audited |
| 5.4.2.6 | Root user umask configured | O | Not explicitly set |
| 5.4.2.7 | System accounts do not have valid login shell | Y | Removed default system users (sync, games, lp, news, etc.) |
| 5.4.2.8 | Accounts without valid login shell are locked | Y | All user accounts locked with `passwd -l` by `access/users.sls` |
| 5.4.3.1 | nologin not listed in /etc/shells | Y | Removed via `sed` in `shell/bash.sls`; guarded with onlyif |
| 5.4.3.2 | Default user shell timeout | O | TMOUT not configured in bash profile |
| 5.4.3.3 | Default user umask configured | Y | umask 0027 set in `/etc/profile.d/umask.sh` and via pam_umask in common-session |

---

### 6 Logging and Auditing

#### 6.1 System Logging

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 6.1.1.1.1 | journald service is active | Y | systemd-journald active by default |
| 6.1.1.1.2 | journald log file access configured | Y | /var/log/journal: root:systemd-journal 2750 |
| 6.1.1.1.3 | journald log file rotation configured | Y | SystemMaxUse, SystemMaxFileSize, MaxRetentionSec set via pillar |
| 6.1.1.1.4 | journald ForwardToSyslog disabled | Y | ForwardToSyslog=no; rsyslog purged |
| 6.1.1.1.5 | journald Storage configured | Y | Storage=persistent |
| 6.1.1.1.6 | journald Compress configured | Y | Compress=yes |
| 6.1.1.2.1 | systemd-journal-remote installed | O | Not installed; no centralised log server configured |
| 6.1.1.2.2 | systemd-journal-upload auth configured | O | Not configured |
| 6.1.1.2.3 | systemd-journal-upload enabled and active | O | Not configured |
| 6.1.1.2.4 | systemd-journal-remote not in use | Y | Not installed; server does not accept remote journal |
| 6.1.2.1 | rsyslog installed | N | rsyslog deliberately purged; journald-only logging strategy |
| 6.1.2.2 | rsyslog service enabled and active | N | See 6.1.2.1 |
| 6.1.2.3 | journald sends logs to rsyslog | N | rsyslog absent by design; ForwardToSyslog=no |
| 6.1.2.4 | rsyslog log file creation mode configured | N | rsyslog not used |
| 6.1.2.5 | rsyslog logging configured | N | rsyslog not used |
| 6.1.2.6 | rsyslog sends logs to remote host | N | rsyslog not used |
| 6.1.2.7 | rsyslog not configured to receive remote logs | N | rsyslog not installed |
| 6.1.2.8 | logrotate configured | N | journald handles rotation natively; no rsyslog log files |
| 6.1.2.9 | rsyslog-gnutls installed | N | rsyslog not used |
| 6.1.2.10 | rsyslog forwarding uses gtls | N | rsyslog not used |
| 6.1.2.11 | rsyslog CA certificates configured | N | rsyslog not used |
| 6.1.3.1 | Access to all logfiles configured | O | journald log dir managed; other log file permissions not audited |

#### 6.2 System Auditing (auditd)

> **Note:** auditd is not yet deployed. This is a known gap. Implementation is planned.

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 6.2.1.1 | auditd packages installed | O | Not yet implemented |
| 6.2.1.2 | auditd service enabled and active | O | Not yet implemented |
| 6.2.1.3 | Auditing for pre-auditd processes enabled | O | Requires `audit=1` kernel parameter |
| 6.2.1.4 | audit_backlog_limit configured | O | Not yet implemented |
| 6.2.2.1 | Audit log storage size configured | O | Not yet implemented |
| 6.2.2.2 | Audit logs not automatically deleted | O | Not yet implemented |
| 6.2.2.3 | System disabled when audit logs full | O | Not yet implemented |
| 6.2.2.4 | System warns when audit logs low on space | O | Not yet implemented |
| 6.2.3.1 | Modification of /etc/sudoers collected | O | Not yet implemented |
| 6.2.3.2 | Actions as another user always logged | O | Not yet implemented |
| 6.2.3.3 | Events modifying sudo log file collected | O | Not yet implemented |
| 6.2.3.4 | Events modifying date/time collected | O | Not yet implemented |
| 6.2.3.5 | sethostname/setdomainname events collected | O | Not yet implemented |
| 6.2.3.6 | Events modifying /etc/issue collected | O | Not yet implemented |
| 6.2.3.7 | Events modifying /etc/hosts collected | O | Not yet implemented |
| 6.2.3.8 | Events modifying network environment collected | O | Not yet implemented |
| 6.2.3.9 | Events modifying /etc/NetworkManager collected | O | Not yet implemented |
| 6.2.3.10 | Use of privileged commands collected | O | Not yet implemented |
| 6.2.3.11 | Unsuccessful file access attempts collected | O | Not yet implemented |
| 6.2.3.12 | Events modifying /etc/group collected | O | Not yet implemented |
| 6.2.3.13 | Events modifying /etc/passwd collected | O | Not yet implemented |
| 6.2.3.14 | Events modifying /etc/shadow and /etc/gshadow collected | O | Not yet implemented |
| 6.2.3.15 | Events modifying /etc/security/opasswd collected | O | Not yet implemented |
| 6.2.3.16 | Events modifying /etc/nsswitch.conf collected | O | Not yet implemented |
| 6.2.3.17 | Events modifying /etc/pam.conf and /etc/pam.d collected | O | Not yet implemented |
| 6.2.3.18 | DAC chmod events collected | O | Not yet implemented |
| 6.2.3.19 | DAC chown events collected | O | Not yet implemented |
| 6.2.3.20 | DAC setxattr events collected | O | Not yet implemented |
| 6.2.3.21 | Successful file system mounts collected | O | Not yet implemented |
| 6.2.3.22 | Session initiation information collected | O | Not yet implemented |
| 6.2.3.23 | Login and logout events collected | O | Not yet implemented |
| 6.2.3.24 | unlink file deletion events collected | O | Not yet implemented |
| 6.2.3.25 | rename file deletion events collected | O | Not yet implemented |
| 6.2.3.26 | Events modifying MAC controls collected | O | Not yet implemented |
| 6.2.3.27 | chcon command attempts collected | O | Not yet implemented |
| 6.2.3.28 | setfacl command attempts collected | O | Not yet implemented |
| 6.2.3.29 | chacl command attempts collected | O | Not yet implemented |
| 6.2.3.30 | usermod command attempts collected | O | Not yet implemented |
| 6.2.3.31 | Kernel module loading/unloading collected | O | Not yet implemented |
| 6.2.3.32 | init_module/finit_module events collected | O | Not yet implemented |
| 6.2.3.33 | delete_module events collected | O | Not yet implemented |
| 6.2.3.34 | query_module events collected | O | Not yet implemented |
| 6.2.3.35 | Audit configuration loaded regardless of errors | O | Not yet implemented |
| 6.2.3.36 | Audit configuration is immutable | O | Not yet implemented |
| 6.2.3.37 | Running and on-disk configuration match | O | Not yet implemented |
| 6.2.4.1 | Audit log files mode configured | O | Not yet implemented |
| 6.2.4.2 | Audit log files owner configured | O | Not yet implemented |
| 6.2.4.3 | Audit log files group owner configured | O | Not yet implemented |
| 6.2.4.4 | Audit log file directory mode configured | O | Not yet implemented |
| 6.2.4.5 | Audit configuration files mode configured | O | Not yet implemented |
| 6.2.4.6 | Audit configuration files owner configured | O | Not yet implemented |
| 6.2.4.7 | Audit configuration files group owner configured | O | Not yet implemented |
| 6.2.4.8 | Audit tools mode configured | O | Not yet implemented |
| 6.2.4.9 | Audit tools owner configured | O | Not yet implemented |
| 6.2.4.10 | Audit tools group owner configured | O | Not yet implemented |

#### 6.3 Integrity Checking (AIDE)

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 6.3.1 | AIDE is installed | O | Not yet implemented |
| 6.3.2 | Filesystem integrity regularly checked | O | Not yet implemented |
| 6.3.3 | Cryptographic mechanisms protect audit tools | O | Not yet implemented |

---

### 7 System Maintenance

#### 7.1 System File and Directory Access

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 7.1.1 | Access to /etc/passwd configured | Y | root:root 0644 via `security/etc-passwd.sls` |
| 7.1.2 | Access to /etc/passwd- configured | Y | root:root 0644 |
| 7.1.3 | Access to /etc/group configured | Y | root:root 0644 |
| 7.1.4 | Access to /etc/group- configured | Y | root:root 0644 |
| 7.1.5 | Access to /etc/shadow configured | Y | root:shadow 0640 |
| 7.1.6 | Access to /etc/shadow- configured | Y | root:shadow 0640 |
| 7.1.7 | Access to /etc/gshadow configured | Y | root:shadow 0640 |
| 7.1.8 | Access to /etc/gshadow- configured | Y | root:shadow 0640 |
| 7.1.9 | Access to /etc/shells configured | Y | root:root 0644 via `shell/bash.sls` |
| 7.1.10 | Access to /etc/security/opasswd configured | Y | root:root 0600 via `security/etc-passwd.sls` |
| 7.1.11 | World writable files and directories secured | O | Not audited by Salt; manual periodic review needed |
| 7.1.12 | No files or directories without owner/group | O | Not audited by Salt |
| 7.1.13 | SUID and SGID files reviewed | O | Not audited; periodic manual review needed |

#### 7.2 Local User and Group Settings

| ID | Topic | Status | Comment |
|----|-------|--------|---------|
| 7.2.1 | Accounts in /etc/passwd use shadowed passwords | Y | Enforced; spurious accounts removed |
| 7.2.2 | /etc/shadow password fields not empty | Y | All user accounts locked with `passwd -l` |
| 7.2.3 | All groups in /etc/passwd exist in /etc/group | Y | Enforced by removing stale accounts |
| 7.2.4 | Shadow group is empty | Y | No users in shadow group |
| 7.2.5 | No duplicate UIDs | Y | Managed user accounts; verified by Salt |
| 7.2.6 | No duplicate GIDs | Y | Managed groups; verified by Salt |
| 7.2.7 | No duplicate user names | Y | Salt user.present is idempotent |
| 7.2.8 | No duplicate group names | Y | Salt group.present is idempotent |
| 7.2.9 | Local interactive user home directories configured | Y | Home dirs created with 0750 permissions |
| 7.2.10 | Local interactive user dot files access configured | O | Dot file permissions not explicitly audited |

---

## ANSSI-BP-028 EN v2.0 — Minimal Level

| ID | Level | Topic | Status | Comment |
|----|-------|-------|--------|---------|
| R1 | M | Choosing and configuring the hardware | O | Out of scope for Salt; handled at infrastructure/procurement level |
| R2 | MI | Configuring the BIOS/UEFI | O | Out of scope for Salt; handled at infrastructure level |
| R3 | MI | Activating UEFI Secure Boot | O | Depends on hosting environment; not managed by Salt |
| R4 | MIEH | Replacing preloaded UEFI keys | N | Requires custom PKI and kernel signing; distribution-signed SHIM used |
| R5 | MI | Configuring a bootloader password | N | Physical console access is organisationally controlled; password would break unattended reboots without IPMI/KVM |
| R6 | MIEH | Protecting kernel command line and initramfs | N | Requires unified kernel image and custom signing; not feasible with distribution kernel |
| R7 | MIE | Activating the IOMMU | O | Hardware-dependent; not managed by Salt |
| R8 | MI | Configuring memory kernel options | O | Boot-time parameters (pti=on, slab_nomerge, etc.) not managed; sysctl-accessible options covered by R9 |
| R9 | MI | Configuring kernel sysctl options | Y | dmesg_restrict, kptr_restrict, randomize_va_space, sysrq, perf paranoid, unprivileged_bpf_disabled set in `99-hardening.conf` |
| R10 | MIE | Disabling kernel module loading | N | Module loading must remain enabled for system functionality and updates |
| R11 | MI | Yama LSM ptrace_scope | Y | kernel.yama.ptrace_scope=1 in `99-hardening.conf` |
| R12 | MI | IPv4 configuration options | Y | Full IPv4 hardening: no forwarding (non-Docker), no redirects, no source route, rp_filter, syncookies, log_martians in `99-hardening.conf` |
| R13 | MI | Disabling IPv6 | Y | IPv6 disabled via net.ipv6.conf.all/default.disable_ipv6=1; pillar kernel:ipv6_disable controls this |
| R14 | MI | Filesystem sysctl configuration | Y | fs.protected_hardlinks, fs.protected_symlinks, fs.protected_fifos=2, fs.protected_regular=2, fs.suid_dumpable=0 |
| R15 | MIEH | Compile options for memory management | N | Distribution kernel used; custom compilation is out of scope |
| R16 | MIEH | Compile options for kernel data structures | N | Distribution kernel used |
| R17 | MIEH | Compile options for memory allocator | N | Distribution kernel used |
| R18 | MIEH | Compile options for kernel module management | N | Distribution kernel used |
| R19 | MIEH | Compile options for abnormal situations | N | Distribution kernel used |
| R20 | MIEH | Compile options for kernel security functions | N | Distribution kernel used |
| R21 | MIEH | Compile options for compiler plugins | N | Distribution kernel used |
| R22 | MIEH | Compile options for IP stack | N | Distribution kernel used |
| R23 | MIEH | Compile options for various kernel behaviors | N | Distribution kernel used |
| R24 | MIEH | Compile options for 32-bit architectures | N | 64-bit system; not applicable |
| R25 | MIEH | Compile options for x86_64 architectures | N | Distribution kernel used |
| R26 | MIEH | Compile options for ARM architectures | N | x86_64 system; not applicable |
| R27 | MIEH | Compile options for ARM 64-bit architectures | N | x86_64 system; not applicable |
| R28 | MI | Typical partitioning | N | Partition layout managed at provisioning time (cloud-init / disk image), not by Salt. Genericcloud image has no separate `/boot` — only `/` and `/boot/efi`. fstab is out of scope for Salt. |
| R29 | MIE | Access restrictions on /boot | Y | `/boot` 0700, `/boot/grub` 0700, kernel/initrd files 0600 root:root via `security/boot.sls` |
| R30 | M | Removing unused user accounts | Y | Default system accounts (sync, games, lp, news, proxy, list, irc) removed by `security/etc-passwd.sls` |
| R31 | M | User password strength | Y | Users have no passwords (locked); SSH key authentication only. Root password policy is organisational |
| R32 | MI | Configuring session timeout | O | TMOUT not configured; SSH ClientAlive provides network-level timeout |
| R33 | MI | Ensuring imputability of administration actions | Y | Dedicated named accounts per administrator; all sudo actions logged to `/var/log/sudo.log`; use_pty enabled |
| R34 | MI | Disabling service accounts | Y | All service accounts have locked passwords and no valid login shell by default |
| R35 | MI | Uniqueness and exclusivity of service accounts | Y | Each installed service uses its own dedicated account (enforced by Debian package conventions; no sharing of `nobody`) |
| R36 | MIE | Changing the default value of UMASK | Y | umask 0027 set in `/etc/profile.d/umask.sh` and via pam_umask in common-session |
| R37 | MIE | Using Mandatory Access Control | Y | AppArmor enabled by default on Debian; active on all running processes with profiles |
| R38 | MIE | Creating a group dedicated to sudo | Y | `sudo` group used; su restricted to sudo group members via pam_wheel |
| R39 | MI | Sudo configuration guidelines | Y | use_pty, logfile, env_reset (default) configured; requiretty not set (intentional: SSH sessions are non-interactive in automation) |
| R40 | MI | Using unprivileged users as sudo targets | O | ALL=(ALL) used in sudoers; targeted unprivileged users not configured |
| R41 | MIE | Limiting EXEC directive in sudo | O | Not explicitly configured |
| R42 | MI | Banishing negations in sudo policies | Y | No negation rules in any sudoers file |
| R43 | MI | Defining arguments in sudo specifications | O | No argument restrictions; ALL commands allowed for sudo group |
| R44 | MI | Editing files securely with sudo (sudoedit) | O | sudoedit not enforced; users may use direct editor via sudo |
| R45 | MIE | Activating AppArmor security profiles | O | Distribution AppArmor profiles present and enforcing for covered daemons; no additional custom profiles written |
| R46 | MIEH | Activating SELinux with targeted policy | N | Debian uses AppArmor; SELinux not installed. AppArmor satisfies R37/R45 |
| R47 | MIEH | Confining unprivileged interactive users (SELinux) | N | SELinux not used; see R46 |
| R48 | MIEH | Setting SELinux boolean variables | N | SELinux not used |
| R49 | MIEH | Uninstalling SELinux debugging tools | N | SELinux not used |
| R50 | MI | Limiting access to sensitive files and directories | Y | /etc/shadow, /etc/gshadow (root:shadow 0640), /etc/passwd, /etc/group (0644), /etc/security/opasswd (0600), SSL private keys (0700) all managed |
| R51 | MIE | Changing secrets and access rights immediately | Y | SSH keys managed via pillar; no default passwords left in place; secrets via SOPS |
| R52 | MI | Securing access to named sockets and pipes | O | Not explicitly managed; individual services use package defaults |
| R53 | M | Avoiding files without known owner/group | N | Not managed by Salt; ownerless files are a runtime/audit concern, not a configuration management concern |
| R54 | M | Setting sticky bit on writable directories | N | /tmp sticky bit is set by default on Debian; auditing all world-writable directories is a runtime concern, not managed by Salt |
| R55 | MI | Dedicating temporary directories to users | O | pam_mktemp / pam_namespace not configured |
| R56 | M | Avoiding setuid/setgid executables | O | Not audited; package-installed setuid binaries not reviewed |
| R57 | MIE | Minimising setuid root and setgid root executables | O | Not audited; periodic manual review needed |
| R58 | M | Installing only strictly necessary packages | Y | APT norecommends/nosuggests enforced; packages purged from `security/packages.sls` |
| R59 | M | Using only official package repositories | Y | Only official Debian repositories configured; no third-party repos |
| R60 | MIE | Using hardened package repositories | O | No hardened repository variant available for Debian stable |
| R61 | M | Updating the system regularly | Y | unattended-upgrades with daily security updates; needrestart for service restarts |
| R62 | M | Disabling non-necessary services | Y | Unwanted services/packages purged; firewall default-deny blocks unexpected listeners |
| R63 | MI | Disabling non-essential service features | Y | SSH DisableForwarding; exim4 local-only mode; no directory indexing or extras |
| R64 | MIE | Configuring service privileges | O | Not systematically analysed; relies on package defaults |
| R65 | MIE | Partitioning services | O | No container/namespace isolation configured |
| R66 | MIEH | Hardening partitioning components | O | No virtualisation layer in use |
| R67 | MI | Secure remote authentication with PAM | Y | pam_faillock enforced; SSH key-only authentication; no cleartext credentials |
| R68 | M | Protecting stored passwords | Y | All user passwords locked; root password stored as hashed shadow entry only; no plaintext credentials |
| R69 | MI | Securing access to remote user databases | N | No remote user databases (LDAP, SQL); local authentication only |
| R70 | MI | Separating system accounts and directory administrator | N | No directory service in use |
| R71 | MIE | Implementing a logging system | Y | systemd-journald with persistent storage; log directory permissions managed |
| R72 | MIE | Implementing dedicated service activity journals | Y | systemd-journald provides per-unit log isolation; each service has its own journal stream |
| R73 | MIE | Logging system activity with auditd | O | auditd not yet deployed; known gap |
| R74 | MI | Hardening the local mail service | Y | exim4-daemon-light configured for local delivery and smarthost relay only; not an open relay |
| R75 | MI | Configuring aliases for service accounts | Y | `/etc/aliases` managed by `mail/exim4/init.sls`; root aliased to admin contact |
| R76 | MIEH | Sealing and checking file integrity | O | AIDE not yet deployed; known gap |
| R77 | MIEH | Protecting the sealing database | O | Depends on R76 |
| R78 | MIE | Partitioning network services | O | All services on one host; no container isolation |
| R79 | MI | Hardening and monitoring exposed services | Y | SSH hardened with strict algorithms, key-only auth, logging; fail2ban active; nftables firewall |
| R80 | M | Minimising the attack surface of network services | Y | nftables default-deny; SSH only on configured port; exim4 bound to loopback only |
