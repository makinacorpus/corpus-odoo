{% set cfg = opts.ms_project %}
{% set data = cfg.data %}
{# NEW VERSION IS NOT WORKING YET #}
{{cfg.name}}-html:
  cmd.run:
    - unless: set -x;which wkhtmltopdf && test "x$(wkhtmltopdf --version|head -n 3|grep wkhtml|awk '{print $2}')" = "x{{data.wkhtml_ver}}"
    - name: |
            set -e
            set -x
            export DPKG_FRONTEND="non-interactive"
            apt-get install -y --force-yes xfonts-75dpi
            # install deps
            apt-get install -y --force-yes wkhtmltopdf
            apt-get remove -y --force-yes  wkhtmltopdf
            cd /tmp
            if [ -e "{{data.wkhtml_arc}}" ];then rm -f "{{data.wkhtml_arc}}";fi
            wget -c "{{data.wkhtml_url}}"
            {% if data.wkhtml_url.endswith('deb') %}
            dpkg -i "{{deb}}"
            apt-get -f install
            {% else %}
            {% set tark = 'z' %}
            {% if "bz2" in data.wkhtml_arc %}{% set tark = 'j' %}{% endif %}
            {% if "xz" in data.wkhtml_arc %}{% set tark = 'J' %}{% endif %}
            tar x{{tark}}vf "{{data.wkhtml_arc}}"
            cd /tmp/wkhtmltox
            rm -f wkhtmltox*deb
            tar czvf ../wkhtmltox.tar.gz .
            {% if ('generic' in data.wkhtml_arc or
                'amd64' in data.wkhtml_arc  or
                'arm' in data.wkhtml_arc  or
                '386' in data.wkhtml_arc
            )%}
            alien --to-deb ../wkhtmltox.tar.gz
            dpkg -i wkhtmltox*deb
            {% else %}
            echo build not yet supported
            exit 1
            #export p=/srv/apps/wkhtml-{{data.wkhtml_ver}}
            #export LDFLAGS="-Wl,-rpath,${p}"
            #./configure --prefix="$p" && make && make install
            #ln -sf "$p/bin/wkhtmltopdf" /usr/local/bin/wkhtmltopdf
            {% endif %}
            {% endif%}
    - use_vt: {{data.use_vt}}
