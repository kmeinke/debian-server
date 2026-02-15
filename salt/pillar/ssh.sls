ssh:
  port: 22
  permit_root_login: 'no'
  password_auth: 'no'
  max_auth_tries: 3
  max_sessions: 3
  allowed_users:
    - admin
