kernel:
  docker_host: False       # set to True if Docker runs on this host — enables ip_forward, disables Docker-incompatible hardening, allows overlayfs
  perf_event_paranoid: 3   # set to 2 for debugging with perf
  sysrq: 0                 # set to 1 for emergency SysRq access
  coredump: False          # set to True to allow core dumps for debugging
