kernel:
  docker_host: False       # set to True if Docker runs on this host — enables ip_forward, disables Docker-incompatible hardening, allows overlayfs
  ipv6_disable: True       # set to False to keep IPv6 enabled (ensure firewall rules cover IPv6)
  perf_event_paranoid: 3   # set to 2 for debugging with perf
  sysrq: 0                 # set to 1 for emergency SysRq access
  coredump: False          # set to True to allow core dumps for debugging
