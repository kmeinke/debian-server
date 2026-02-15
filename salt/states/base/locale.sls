{% set timezone = salt['pillar.get']('locale:timezone', 'Europe/Berlin') %}
{% set locale = salt['pillar.get']('locale:lang', 'en_US.UTF-8') %}

set_timezone:
  timezone.system:
    - name: {{ timezone }}

generate_locale:
  locale.present:
    - name: {{ locale }}

set_default_locale:
  locale.system:
    - name: {{ locale }}
