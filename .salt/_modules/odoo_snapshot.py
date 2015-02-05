#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
__docformat__ = 'restructuredtext en'

import os

from pprint import pprint


def local_snapshot(data_dir=None,
                   backup_dir=None,
                   url=None,
                   project='odoo',
                   keep=20, *a, **kw):
    """."""
    _s = __salt__
    try:
        cfg = _s['mc_project.get_configuration'](project)
    except Exception:
        cfg = {}
    if not data_dir:
        data_dir = cfg['data_root']
    if not backup_dir:
        backup_dir = os.path.join(data_dir, 'snapshots')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    if not url:
        url = ('postgresql://{0[db_user]}:{0[db_password]}'
               '@{0[db_host]}:{0[db_port]}/'
               '{0[db_name]}').format(cfg['data'])
    backups = [
        '{0}'.format(a)
        for a in reversed(
            sorted([int(i) for i in os.listdir(backup_dir)]))]
    to_keep = backups[:keep]
    for i in [a for a in backups if a not in to_keep]:
        _s['file.remove'](os.path.join(backup_dir, i))
    curb = "{0}".format(max([int(a) for a in backups]) + 1)
    fcurb = os.path.join(backup_dir, curb)
    if not os.path.exists(fcurb):
        os.makedirs(fcurb)
    elif os.listdir(fcurb):
        raise ValueError('Already existing backup {0}'.format(fcurb))
    ret = _s['cmd.run_all'](
        'tar cjf {0}/data.tbz2 .'.format(fcurb),
        cwd=cfg['data']['odoo_data'])
    if ret['retcode']:
        pprint(ret)
        raise ValueError('backup failed tar')
    ret = _s['cmd.run_all']('pg_dump -Fc '
                            ' -d {0[db_name]}'
                            ' -h {0[db_host]}'
                            ' -p {0[db_port]}'
                            ' -U {0[db_user]}'
                            ' > dump.sql'.format(cfg['data']),
                            env={"PGPASSWORD": cfg['data']['db_password']},
                            cwd=fcurb)
    if ret['retcode']:
        print(_s['mc_utils.output'](ret, outputter='nested'))
        raise ValueError('backup failed dump')
    return True


def ssh_snapshot(data_dir=None,
             backup_dir=None,
             url=None,
             project='odoo',
             keep=20, *a, **kw):
    """."""
    _s = __salt__
    try:
        cfg = _s['mc_project.get_configuration'](project)
    except Exception:
        cfg = {}
    if not data_dir:
        data_dir = cfg['data_root']
    if not backup_dir:
        backup_dir = os.path.join(data_dir, 'snapshots')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    if not url:
        url = ('postgresql://{0[db_user]}:{0[db_password]}'
               '@{0[db_host]}:{0[db_port]}/'
               '{0[db_name]}').format(cfg['data'])
    backups = [
        '{0}'.format(a)
        for a in reversed(
            sorted([int(i) for i in os.listdir(backup_dir)]))]
    to_keep = backups[:keep]
    for i in [a for a in backups if a not in to_keep]:
        _s['file.remove'](os.path.join(backup_dir, i))
    curb = "{0}".format(max([int(a) for a in backups]) + 1)
    fcurb = os.path.join(backup_dir, curb)
    if not os.path.exists(fcurb):
        os.makedirs(fcurb)
    elif os.listdir(fcurb):
        raise ValueError('Already existing backup {0}'.format(fcurb))
    ret = _s['cmd.run_all'](
        'tar cjf {0}/data.tbz2 .'.format(fcurb),
        cwd=cfg['data']['odoo_data'])
    if ret['retcode']:
        pprint(ret)
        raise ValueError('backup failed tar')
    # the backup cmd is in authorizedkeys on other side
    # command="PGPASSWORD="" pg_dump -Fc --ignore-version -d odoo_prod -h 127.0.0.1 -p 5432 -U odoo_prod" ssh-rsa  ...
    ret = _s['cmd.run_all']('ssh -i ../../key {0[db_host]}'
                            ' "pg_dump"> dump.sql'.format(cfg['data']),
                            env={"PGPASSWORD": cfg['data']['db_password']},
                            cwd=fcurb)
    if ret['retcode']:
        print(_s['mc_utils.output'](ret, outputter='nested'))
        raise ValueError('backup failed dump')
    return True


def snapshot(*a, **kw):
    return local_snapshot(*a, **kw)

# vim:set et sts=4 ts=4 tw=80:
