{% set timezone = salt['pillar.get']('locale:timezone', 'Europe/Berlin') %}
{% set locale = salt['pillar.get']('locale:lang', 'en_US.UTF-8') %}

locales:
  pkg.installed: []

set_timezone:
  timezone.system:
    - name: {{ timezone }}

generate_locale:
  locale.present:
    - name: {{ locale }}
    - require:
      - pkg: locales

ensure_default_locale_file:
  file.managed:
    - name: /etc/default/locale
    - contents: 'LANG={{ locale }}'
    - require:
      - locale: generate_locale

set_default_locale:
  locale.system:
    - name: {{ locale }}
    - require:
      - file: ensure_default_locale_file
