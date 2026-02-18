# Fail fast if secrets pillar is not loaded
secrets_pillar_check:
  test.check_pillar:
    - present:
      - secrets
    - failhard: True
