{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set cfg = opts.ms_project %}
{% set data = cfg.data %}


{{cfg.name}}-install-api:
  cmd.run:
    - name: /salt-venv/salt/bin/pip install "OERPLib==0.8.4"
    - unless: test -e /salt-venv/salt/lib/python2.7/site-packages/OERPLib-0.8.4-py2.7.egg-info
