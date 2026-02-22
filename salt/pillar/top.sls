base:
  # Global defaults — applied to every host
  '*':
    - defaults/network
    - defaults/locale
    - defaults/contact
    - defaults/users
    - defaults/ssh
    - defaults/mail
    - defaults/apt
    - defaults/firewall
    - defaults/fail2ban
    - defaults/kernel
    - defaults/logging
    - defaults/nginx

  # Test hosts
  'test_docker_*':
    - hosts/test_docker
    - secrets/hosts/test_docker

  'test_hetzner_*':
    - hosts/test_hetzner
    - secrets/hosts/test_hetzner

  'test_oci_*':
    - hosts/test_oci
    - secrets/hosts/test_oci
