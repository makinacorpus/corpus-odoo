#!/usr/bin/env bash
{%- set cfg = salt['mc_project.get_configuration'](project) %}
{%- set data = cfg.data %}
. "{{data.py_root}}/bin/activate"
cd "{{cfg.project_root}}/src/odoo"
if [ -e odoo-bin ];then
    exec ./odoo-bin --config="{{cfg.data_root}}/openerp_rc" "${@}"
else
    exec ./odoo.py --config="{{cfg.data_root}}/openerp_rc" "${@}"
fi
