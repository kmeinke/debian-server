kernel:
  ip_forward: 0            # set to 1 if Docker runs on host
  perf_event_paranoid: 3   # set to 2 for debugging with perf
  sysrq: 0                 # set to 1 for emergency SysRq access
  coredump: False          # set to True to allow core dumps for debugging
