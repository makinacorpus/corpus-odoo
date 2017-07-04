{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set cfg = opts.ms_project %}
{% set data = cfg.data %}

include:
  - makina-states.services.monitoring.circus

{% for config, cdata in data.configs.items() %}
{% set config = salt['mc_utils.format_resolve'](config, cfg) %}
{{cfg.name}}-{{config}}-config:
  file.managed:
    - name: "{{config}}"
    - source: "{{cdata.template}}"
    - template: jinja
    - user: {{cdata.get('user', cfg.user)}}
    - defaults:
        project: "{{cfg.name}}"
    - group: {{cdata.get('group', cfg.group)}}
    - mode: "{{cdata.get('mode', "0600")}}"
    - makedirs: true
{%endfor%}

{% set circus_data = {
  'cmd': '{0}/odoo_wrapper.sh'.format(cfg.data_root),
  'environment': cfg.data.shell_env,
  'uid': cfg.user,
  'gid': cfg.group,
  'copy_env': True,
  'manager_force_reload': true,
  'working_dir': "{0}/src/odoo".format(cfg.project_root),
  'warmup_delay': "10",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher(cfg.name+'-odoo', **circus_data) }}


{{cfg.name}}-crons:
  file.managed:
    - name: /etc/cron.d/{{cfg.name}}_crons
    - contents: |
                0 0 * * * root find {{data.odoo_data}}/sessions -type f -mtime +30  -delete >/dev/null 2>&1
    - mode: 600
    - user: root
    - group: root
