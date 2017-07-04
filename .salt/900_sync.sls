{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set cfg = opts.ms_project %}
{% set data = cfg.data %}


{% if data.sync_enabled %}
{{cfg.name}}-install-api:
  cmd.run:
    - name: /srv/makina-states/venv/salt/bin/pip install "OERPLib==0.8.4"
    - unless: test -e /salt-venv/salt/lib/python2.7/site-packages/OERPLib-0.8.4-py2.7.egg-info

{{cfg.name}}-cron:
  file.managed:
    - name: "/etc/cron.d/{{cfg.name}}ldap_cron"
    - contents: |
                0 */1 * * * root su -c ". /etc/profile;salt-call -lquiet  --local odoo_ldap.ldap_sync >/dev/null 2>&1"
    - user: root
    - group: root
    - mode: 050
{% else %}
{{cfg.name}}-cron:
  file.absent:
    - name: "/etc/cron.d/{{cfg.name}}ldap_cron"
{% endif %}
