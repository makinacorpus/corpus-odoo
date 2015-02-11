#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
__docformat__ = 'restructuredtext en'

import os
import datetime

from pprint import pprint
import salt.utils.odict
import logging
import oerplib


log = logging.getLogger(__name__)
_marker = object()


def query(uri, search=None, retrieve_attributes=None, **kw):
    '''

    ::

        odoo_ldap.query ldap://ldap.foo.net base="dc=foo,dc=net" \\
                [search="(&(objectClass=person)(objectClass=top))"] \\
                [scope="subtree"] \\
                [user="foo"] [password="bar"]

    '''
    with __salt__['mc_ldap.get_handler'](uri, **kw) as handler:
        results = handler.query(search,
                                retrieve_attributes=retrieve_attributes,
                                base=kw.get('base', None),
                                scope=kw.get('scope', None))
        return results


def get_or_create_user(self, cr, uid, conf, login, ldap_entry,
                       context=None):
        """
        Retrieve an active resource of model res_users with the specified
        login. Create the user if it is not initially found.

        :param dict conf: LDAP configuration
        :param login: the user's login
        :param tuple ldap_entry: single LDAP result (dn, attrs)
        :return: res_users id
        :rtype: int
        """

        user_id = False
        login = tools.ustr(login.lower().strip())
        cr.execute("SELECT id, active FROM res_users WHERE lower(login)=%s", (login,))
        res = cr.fetchone()
        if res:
            if res[1]:
                user_id = res[0]
        elif conf['create_user']:
            log.debug("Creating new Odoo user \"%s\" from LDAP" % login)
            user_obj = self.pool['res.users']
            values = self.map_ldap_attributes(cr, uid, conf, login, ldap_entry)
            if conf['user']:
                values['active'] = True
                user_id = user_obj.copy(cr, SUPERUSER_ID, conf['user'],
                                        default=values)
            else:
                user_id = user_obj.create(cr, SUPERUSER_ID, values)
        return user_id

def ldap_sync(project='odoo', *p_a, **kw):
    """."""
    _s = __salt__
    cfg = _s['mc_project.get_configuration'](project)
    data = cfg['data']
    conn_kw = {}
    for i, l in {
        'uri': 'ldap_url',
        'user': 'ldap_reader',
        'base': 'ldap_users_base',
        'password': 'ldap_reader_pw'
    }.items():
        v = data.get(l, _marker)
        if v is _marker and i not in ['uri']:
            continue
        conn_kw[i] = v

    _ms = __salt__['mc_utils.magicstring']
    users = query(conn_kw.pop('uri'), data['ldap_users_filter'], **conn_kw)
    oerp = oerplib.OERP(data['odoo_api'],
                        data['odoo_port'],
                        data['odoo_proto'])
    admin = oerp.login('admin', data['admin_password'], data['odoo_base'])
    #stz = oerp.common.timezone_get('admin',
    #                               data['admin_password'],
    #                               data['odoo_base'])
    import time
    users_obj = oerp.get('res.users')
    employees_obj = oerp.get('hr.employee')
    partners_obj = oerp.get('res.partner')
    company_id = data['odoo_company_id']
    snow = datetime.datetime.now()
    snow = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
    tz = 'Europe/Paris'
    lang = 'fr_FR'
    for user in users:
        if user not in ['admin'] + data.get('odoo_skipped_users', []):
            dn, udata = user
            tri = udata['uid'][0]
            city = udata.get('l', [])
            employeeType = udata.get('employeeType', [])
            if employeeType:
                employeeType = employeeType[0]
            else:
                employeeType = None
            if city:
                city = city[0]
                city = {'nantes': 'Nantes',
                        'toulouse': 'Toulouse',
                        'caen': 'Caen',
                        'pau': 'Pau'}.get(city, data['odoo_town'])
            else:
                city = None
            firstname, lastname = (
                _ms(udata['givenName'][0]), _ms(udata['sn'][0]))
            mails = udata.get('mail', [])
            if not isinstance(mails, list):
                mails = []
            for m in udata.get('gosaMailAlternateAddress', []):
                mails.append(m)
            mails = __salt__['mc_utils.uniquify'](mails)
            name = '{0} {1}'.format(_ms(firstname), _ms(lastname))
            pdata = {'name': name,
                     'display_name': name,
                     'tz': tz,
                     'city': city,
                     'company_id': company_id,
                     'create_uid': 1,
                     'lang': lang,
                     'customer': False,
                     'employee': True,
                     'active': True,
                     'type': 'contact',
                     'use_parent_address': False,
                     'write_date': snow,
                     'email': udata['mail'][0],
                     'function': employeeType,
                     'create_date': snow,
                     'color': 0}
            odata = {'active': True,
                     'login': tri,
                     'password': None,
                     'password_crypt': None,
                     'company_id': company_id,
                     'create_uid': 1,
                     'write_uid': 1,
                     'create_date': snow,
                     'login_date': snow,
                     'share': False,
                     'write_date': snow,
                     'display_groups_suggestions': True}
            edata = {'name': name,
                     'work_email': mails[0]}
            lname = name.lower()
            try:
                pid = partners_obj.search([('name', 'ilike', name)])[0]
            except IndexError:
                pid = None
                try:
                    for m in mails:
                        try:
                            pid = partners_obj.search(
                                [('email', 'ilike', m)])[0]
                        except IndexError:
                            continue
                    if pid is None:
                        raise IndexError('')
                except IndexError:
                    pid = partners_obj.create(pdata)
                    log.info('Creating parter for {0}'.format(name))
            pobj = [a for a in partners_obj.browse([pid])][0]
            odata['partner_id'] = pid
            try:
                uid = users_obj.search(
                    [('login', 'ilike', udata['uid'][0])])[0]
            except IndexError:
                uid = None
                try:
                    for m in mails:
                        try:
                            uid = users_obj.search([('login', 'ilike', m)])[0]
                        except IndexError:
                            # user does not exists, create it
                            continue
                    if uid is None:
                        raise IndexError('')
                except IndexError:
                    uid = users_obj.create(odata)
                    log.info('Creating user for {0}'.format(name))
            try:
                eid = employees_obj.search(
                    [('login', 'ilike', udata['uid'][0])])[0]
            except IndexError:
                eid = None
                try:
                    for m in mails:
                        try:
                            eid = employees_obj.search(
                                [('work_email', 'ilike', m)])[0]
                        except IndexError:
                            # user does not exists, create it
                            continue
                    if eid is None:
                        eid = employees_obj.search(
                            [('name', 'ilike', name)])[0]
                except IndexError:
                    eid = employees_obj.create(edata)
                    log.info('Creating employee for {0}'.format(name))
            eobj = [a for a in employees_obj.browse([eid])][0]
            uobj = [a for a in users_obj.browse([uid])][0]
            pdata['user_id'] = uid
            odata['partner_id'] = pid
            log.info('Updating partner: {1}/{0}'.format(pobj.id, name))
            oerp.write('res.partner', [pobj.id], pdata)
            log.info('Updating employee: {0}'.format(uobj.id))
            oerp.write('hr.employee', [eobj.id], edata)
            log.info('Updating user: {0}'.format(uobj.id))
            oerp.write('res.users', [uobj.id], odata)
# vim:set et sts=4 ts=4 tw=80:
