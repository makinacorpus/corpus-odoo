{% set cfg = opts.ms_project %}
{% set data = cfg.data %}
{{cfg.name}}-change-admin-pw:
  cmd.run:
    - user: {{cfg.user}}
    - cwd:   {{cfg.project_root}}/src/odoo
    - name: |
            set -e
            . "{{data.py_root}}/bin/activate"
            pw=$(python -c "
            import sys;sys.path.append('addons')
            from auth_crypt.auth_crypt import default_crypt_context
            print(default_crypt_context.encrypt('{{data.admin_password}}'))
            ")
            echo "UPDATE res_users SET password=null, password_crypt='${pw}' WHERE login in ('demo', 'admin');" \
              | psql -v ON_ERROR_STOP=1 "{{data.psql_url}}"
