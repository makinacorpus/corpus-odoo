#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import time
import os
import datetime
import traceback

from pprint import pprint
import salt.utils.odict
import logging
import oerplib


from mc_states.api import six

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


def sanitized_data(data):
    data = copy.deepcopy(data)
    for i in [a for a in data]:
        val = data[i]
        if (
            isinstance(val, list) and
            len(val) == 2 and
            isinstance(val[0], int) and
            isinstance(val[1], six.string_types)
        ):
            data[i] = val[0]
        if (
            i.endswith('id') or
            i.endswith('ids')
        ):
            data.pop(i, None)
    return data


def update_obj(oerp, obj, data):
    try:
        for i, val in six.iteritems(sanitized_data(data)):
            if i in ['id']:
                continue
            setattr(obj, i, val)
        return oerp.write_record(obj)
    except Exception, ex:
        import pdb;pdb.set_trace()  ## Breakpoint ##
        trace = traceback.format_exc()
        print(trace)
        raise


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
    ldap_uri = conn_kw.pop('uri')
    users = query(ldap_uri,
                  data['ldap_users_filter'], **conn_kw)
    ex_users = query(ldap_uri,
                     data['ldap_ex_users_filter'], **conn_kw)
    oerp = oerplib.OERP(data['odoo_api'],
                        data['odoo_port'],
                        data['odoo_proto'])
    admin = oerp.login('admin', data['admin_password'], data['odoo_base'])
    #stz = oerp.common.timezone_get('admin',
    #                               data['admin_password'],
    #                               data['odoo_base'])
    users_obj = oerp.get('res.users')
    employees_obj = oerp.get('hr.employee')
    partners_obj = oerp.get('res.partner')
    company_id = data['odoo_company_id']
    snow = datetime.datetime.now()
    snow = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
    ex_uids = []
    [ex_uids.extend(a[1]['uid']) for a in ex_users]
    tz = 'Europe/Paris'
    lang = 'fr_FR'
    employee_skipped_properties = ['remaining_leaves']
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
            active = True
            log.info(
                '- On {0} {1}'.format(_ms(firstname), _ms(lastname)))
            if tri in ex_uids:
                active = False
            pdata = {'name': name,
                     'display_name': name,
                     'tz': tz,
                     'ci:vty': city,
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
            odata = {'active': active,
                     'login': tri,
                     'password': None,
                     'password_crypt': None,
                     'company_id': company_id,
                     'name': name,
                     'create_uid': 1,
                     'write_uid': 1,
                     'create_date': snow,
                     'login_date': snow,
                     'share': False,
                     'write_date': snow,
                     'display_groups_suggestions': True}
            edata = {'name': name,
                     'active': active,
                     'work_email': mails[0]}
            synced_pdata = {'name': name,
                            'display_name': name,
                            'active': True,
                            'email': udata['mail'][0]}
            synced_odata = {'active': active,
                            'login': tri}
            synced_edata = {'name': name,
                            'active': active,
                            'work_email': mails[0]}
            # create user
            sodata, uobj, uid = None, None, None
            try:
                uid = users_obj.search(
                    [('login', 'ilike', udata['uid'][0]),
                     ('active', 'in', [True, None, False])])[0]
            except IndexError:
                uid = None
                try:
                    for m in mails:
                        try:
                            uid = users_obj.search([
                                ('login', 'ilike', m),
                                ('active', 'in', [True, None, False])])[0]
                            break
                        except IndexError:
                            # user does not exists, create it
                            continue
                    if uid is None:
                        raise IndexError('')
                except IndexError:
                    uid = users_obj.create(odata)
                    log.info('Creating user for {0}'.format(name))
            uobj = [a for a in users_obj.browse([uid])][0]
            sodata = [a for a in users_obj.read([uid])][0]
            # search employee
            sedata, eobj, eid = None, None, None
            employees = {}
            try:
                for e in employees_obj.search(
                    [('login', 'ilike', udata['uid'][0]),
                     ('active', 'in', [True, None, False])]
                ):
                    employees[e] = None
            except IndexError:
                try:
                    for e in employees_obj.search(
                        [('name', 'ilike', name),
                         ('active', 'in', [True, None, False])]):
                        employees[e] = None
                except IndexError:
                    pass
            for m in mails:
                try:
                    for e in employees_obj.search([
                        ('active', 'in', [True, None, False]),
                        ('work_email', 'ilike', m)
                    ]):
                        employees[e] = None
                except IndexError:
                    continue
            for eeid in [a for a in employees]:
                employee = employees[eeid]
                if employee:
                    continue
                employees[eeid] = [a for a in employees_obj.read([eeid])][0]
            for eeid, employee in six.iteritems(employees):
                # search employee linked to user
                try:
                    if (
                        uid and
                        employee.get('user_id', [None])[0] == uid and
                        employee.get('active')
                    ):
                        eid = eeid
                        break
                except (ValueError, TypeError, IndexError, AttributeError):
                    continue
            # create employee if not existing
            employee_created = False
            if not eid:
                log.info('Creating employee for {0}'.format(name))
                eid = employees_obj.create(edata)
                employee_created = True
            if not eid:
                raise ValueError('no employee for {0}'.format(udata['name']))
            eobj = [a for a in employees_obj.browse([eid])][0]
            sedata = [a for a in employees_obj.read([eid])][0]
            # search partner
            spdata, pobj, pid = None, None, None
            if sodata.get('partner_id'):
                try:
                    pobj = [a for a in partners_obj.browse(
                        [sodata['partner_id'][0]])][0]
                    spdata = [a for a in partners_obj.read(
                        [sodata['partner_id'][0]])][0]
                    pid = sodata['partner_id'][0]
                except IndexError:
                    continue
            if not pid:
                try:
                    pid = partners_obj.search([('name', 'ilike', name)])[0]
                except IndexError:
                    pid = None
                    try:
                        for m in mails:
                            try:
                                pid = partners_obj.search(
                                    [('email', 'ilike', m)])[0]
                                break
                            except IndexError:
                                continue
                        if pid is None:
                            raise IndexError('')
                    except IndexError:
                        pass
            if not pid:
                log.info('Creating parter for {0}'.format(name))
                pid = partners_obj.create(pdata)
            if not pid:
                raise ValueError('no partner for {0}'.format(udata['name']))
            pobj = [a for a in partners_obj.browse([pid])][0]
            spdata = [a for a in partners_obj.read([pid])][0]
            # search delta
            for idata, real_data, synced_data in (
                (pdata, spdata, synced_pdata),
                (odata, sodata, synced_odata),
                (edata, sedata, synced_edata),
            ):
                for i in [a for a in synced_data]:
                    overwrite = False
                    if synced_data[i] != real_data[i]:
                        overwrite = True
                        try:
                            if (
                                isinstance(synced_data[i],
                                           six.string_types) and
                                isinstance(real_data[i], six.string_types) and
                                (_ms(real_data[i]) == _ms(synced_data[i]))
                            ):
                                overwrite = False
                        except Exception:
                            pass
                    if overwrite:
                        real_data[i] = synced_data[i]
                    else:
                        synced_data.pop(i, None)
            if spdata['user_id'] and spdata['user_id'][0] != uid:
                synced_data['user_id'] = spdata['user_id'] = uid
            if sodata['partner_id'] and sodata['partner_id'][0] != pid:
                synced_data['partner_id'] = sodata['partner_id'] = pid
            if (
                employee_created and
                ((not sedata['user_id']) or
                 (sedata['user_id'][1] != uid))
            ):
                synced_edata['user_id'] = sedata['user_id'] = uid
            for i in [a for a in employee_skipped_properties if a in sedata]:
                sedata.pop(i, None)
            # XXX: M2M are setted directly on employee & partner, do no mess
            # the reverse as the orm breaks and dont resolve them
            for i in [
                # 'user_id',
                # 'employee_id',
                'user_ids',
                'employee_ids'
            ]:
                sodata.pop(i, None)
            for syncdata in [sodata, spdata, sedata]:
                # workaround:
                # ValueError: 'property_account_receivable' field is required
                for i in [a for a in syncdata]:
                    val = syncdata[i]
                    if i.startswith('property_') and not val:
                        syncdata.pop(i, None)
            if synced_pdata:
                log.info('Updating partner: {0}'.format(pobj.id))
                update_obj(oerp, pobj, spdata)
            if synced_edata:
                log.info('Updating employee: {0}'.format(eobj.id))
                update_obj(oerp, eobj, sedata)
            if synced_odata:
                log.info('Updating user: {0}'.format(uobj.id))
                update_obj(oerp, uobj, sodata)
# vim:set et sts=4 ts=4 tw=80:
