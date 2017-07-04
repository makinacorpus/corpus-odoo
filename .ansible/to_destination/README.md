# Reset a odoo install from another one

- Execute the script inside the directory

	```
	cd /path/to/.ansible/to_destinatio n
	cp inventory.sample inventory
	cp .ansible/to_destination/group_vars/all/100_overrides.sample.yml \
		.ansible/to_destination/group_vars/all/100_overrides.yml
	```

- Dump & push database to env

	```
	/srv/corpusops/corpusops.bootstrap/bin/ansible-playbook \
		-vvvv  site.yml  --tags=push_db
	```

- Load dump

	```
	/srv/corpusops/corpusops.bootstrap/bin/ansible-playbook \
      -vvvv  site.yml  --tags=load_db

- Sync code/addons

	```
	/srv/corpusops/corpusops.bootstrap/bin/ansible-playbook \
		-vvvv  site.yml  --tags=sync_code,sync_addons
    ```

- Sync file store

	```
	/srv/corpusops/corpusops.bootstrap/bin/ansible-playbook \
		-vvvv  site.yml  --tags=sync_files
	```
    ```

- everything

	```
	/srv/corpusops/corpusops.bootstrap/bin/ansible-playbook \
		-vvvv  site.yml
	```
