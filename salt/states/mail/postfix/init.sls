postfix:
  pkg.installed:
    - pkgs:
      - postfix
      - mailutils
      - libsasl2-modules

postfix_service:
  service.running:
    - name: postfix
    - enable: True
    - onlyif: test -d /run/systemd/system
    - require:
      - pkg: postfix

/etc/postfix/main.cf:
  file.managed:
    - source: salt://mail/postfix/files/main.cf
    - template: jinja
    - mode: '0644'
    - user: root
    - group: root
    - require:
      - pkg: postfix
    - watch_in:
      - service: postfix_service

/etc/postfix/sasl:
  file.directory:
    - mode: '0750'
    - user: root
    - group: root
    - require:
      - pkg: postfix

/etc/postfix/sasl/sasl_passwd:
  file.managed:
    - contents_pillar: secrets:mail:sasl_passwd
    - show_changes: False
    - mode: '0600'
    - user: root
    - group: root
    - require:
      - file: /etc/postfix/sasl

postmap_sasl_passwd:
  cmd.wait:
    - name: postmap hash:/etc/postfix/sasl/sasl_passwd
    - watch:
      - file: /etc/postfix/sasl/sasl_passwd
    - watch_in:
      - service: postfix_service

/etc/aliases:
  file.managed:
    - source: salt://mail/postfix/files/aliases
    - template: jinja

newaliases:
  cmd.wait:
    - name: newaliases
    - watch:
      - file: /etc/aliases
