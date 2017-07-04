{% set cfg = opts.ms_project %}
{% set data = cfg.data %}
{% set purl = "postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}".format(**data) %}
{{cfg.name}}-change-admin-pw:
  cmd.run:
    - user: {{cfg.user}}
    - use_vt: {{data.use_vt}}
    - name: |
            cd {{cfg.project_root}}/src/odoo
            set -e
            # {{data.odoo_rev}}
            p=$(pwd)
            . "{{data.py_root}}/bin/activate"
            pw=$(python -c "
            import sys;
            sys.path.append('{{cfg.project_root}}/src/odoo');
            {% if data.odoo_rev|float > '8.0'|float %}
            sys.path.append('{{cfg.project_root}}/src/odoo/addons');
            sys.path.append('{{cfg.project_root}}/src/odoo/odoo/addons');
            import odoo.addons.base;
            from auth_crypt.models.res_users import default_crypt_context;
            {% else %}
            import openerp.addons.base;
            from auth_crypt.auth_crypt import default_crypt_context;
            {% endif %}

            print(default_crypt_context.encrypt('{{data.admin_password}}'))
            ")
            echo "UPDATE res_users SET password=null, password_crypt='${pw}' WHERE login in ('demo', 'admin');" \
              | psql -v ON_ERROR_STOP=1 "{{purl}}";
            {#
            echo "update ir_config_parameter set value='{{data.domain}}' where key='mail.catchall.domain';" \
              | psql -v ON_ERROR_STOP=1 "{{purl}}"
            echo "update ir_config_parameter set value='http://{{data.domain}}' where key='web.base.url';" \
              | psql -v ON_ERROR_STOP=1 "{{purl}}"
            #}
