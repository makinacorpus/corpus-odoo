{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set cfg = opts.ms_project %}
{% set data = cfg.data %}

include:
  - makina-states.services.monitoring.circus 

{{cfg.name}}-install-api:
  cmd.run:
    - name: /salt-venv/bin/pip install "OERPLib==0.8.4"
    - unless: test -e /salt-venv/lib/python2.7/site-packages/OERPLib-0.8.4-py2.7.egg-info
