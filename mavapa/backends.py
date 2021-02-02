#!/usr/bin/env python
import os
import hashlib
import ldap
from codecs import encode
from base64 import b64encode
from anytree import Node
from anytree.exporter import DictExporter


class LDAP():
    def __init__(self, **kwargs):
        # Loading defaults connection options
        kwargs.setdefault('host', 'localhost')
        kwargs.setdefault('port', 389)
        kwargs.setdefault('binddn', '')
        kwargs.setdefault('bindpw', '')
        kwargs.setdefault('bytes_mode', False)
        self.copt = kwargs.copy()
        # Connect with the defaults options
        self.connect()

    def connect(self, **kwargs):
        self.copt.update(kwargs)
        try:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            self.cstr = ldap.initialize(
                self.copt['host'],
                bytes_mode=self.copt['bytes_mode']
            )
            self.cstr.set_option(
                ldap.OPT_X_TLS_REQUIRE_CERT,
                ldap.OPT_X_TLS_NEVER
            )
            self.cstr.set_option(ldap.OPT_REFERRALS, 0)
            self.cstr.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            self.cstr.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
            self.cstr.set_option(ldap.OPT_X_TLS_DEMAND, True)
            self.cstr.set_option(ldap.OPT_DEBUG_LEVEL, 255)
            if all(map(lambda x: self.copt[x] != '', ['binddn', 'bindpw'])):
                self.cstr.simple_bind_s(
                    self.copt['binddn'], self.copt['bindpw']
                )
        except ldap.INVALID_CREDENTIALS:
            print(ldap.INVALID_CREDENTIALS)
        except ldap.SERVER_DOWN:
            print(ldap.SERVER_DOWN)
        except ldap.LDAPError:
            print(ldap.LDAPError)

    def disconnect(self):
        try:
            self.cstr.unbind()
        except ldap.LDAPError as e:
            print(e)

    def auth(self, username, password):
        try:
            conn = ldap.initialize(self.copt['host'])
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.simple_bind_s(username, password)
            return True
        except ldap.LDAPError:
            conn.unbind_s()
            return False

    def tree(self, **kwargs):
        kwargs.setdefault('filter', '(objectClass=*)')
        kwargs.setdefault('limit', -1)
        query = self.query(**kwargs)
        exporter = DictExporter()
        root = Node(kwargs['basedn'], dn=kwargs['basedn'])
        if query:
            res = []
            for x in query:
                if not kwargs['basedn'] == x[0]:
                    entries = (
                        x[0].replace(',%s' % (kwargs['basedn']), '')
                    ).split(',')
                    entries.reverse()
                    res.append(','.join(entries))
            res.sort()
            for dn in res:
                entries = dn.split(',')
                parent = root
                for e in entries:
                    node = None
                    for c in parent.children:
                        if c.name == e:
                            node = c
                    if not node:
                        node = Node(
                            e, parent=parent, dn=','.join([e, parent.dn])
                        )
                    parent = node
        return exporter.export(root)

    def query(self, **kwargs):
        codec = 'utf-8'
        kwargs.setdefault('basedn', u'')
        kwargs.setdefault('filter', '(objectclass=person)')
        kwargs.setdefault('attrs', ['*'])
        kwargs.setdefault('scope', ldap.SCOPE_SUBTREE)
        kwargs.setdefault('limit', 25)
        kwargs.setdefault('exclude', [])
        kwargs.setdefault('dn', False)
        try:
            rows = []
            if not kwargs['dn']:
                kwargs['attrs'] = [
                    encode(a).decode(codec) for a in kwargs['attrs']
                ]
                data = self.cstr.search(
                    encode(kwargs['basedn']).decode(codec), kwargs['scope'],
                    encode(kwargs['filter']).decode(codec), kwargs['attrs']
                )
                res = []
                while 1:
                    rtype, rdata = self.cstr.result(data, 0)
                    if (rdata == []):
                        break
                    else:
                        if rtype == ldap.RES_SEARCH_ENTRY:
                            for i in rdata:
                                res.append(i)
            else:
                res = self.cstr.search_s(kwargs['filter'], kwargs['scope'])

            for idx in res:
                entry = {}
                for attr in idx[1]:
                    if attr not in kwargs['exclude']:
                        entry[attr] = []
                        for a in idx[1][attr]:
                            try:
                                e = a.decode(codec)
                            except Exception:
                                e = b64encode(a).decode(codec)
                            entry[attr].append(e)
                rows.append((idx[0], entry))
        except ldap.LDAPError:
            print(ldap.LDAPError)
        except Exception as e:
            print(str(e))
        return rows

    def modify(self, dn, dict_new, dict_old={}):
        codec = 'utf-8'
        tasks = []
        for i in dict_new:
            attr_new = [encode(dict_new[i], codec)]
            if i in dict_old:
                if dict_old[i] == '*':
                    tasks.append((ldap.MOD_REPLACE, i, attr_new))
                else:
                    attr_old = [encode(dict_old[i], codec)]
                    tasks.append((ldap.MOD_DELETE, i, attr_old))
                    tasks.append((ldap.MOD_ADD, i, attr_new))
            else:
                tasks.append((ldap.MOD_ADD, i, dict_new[i]))

        print(dn, tasks)
        self.cstr.modify_s(dn, tasks)

    def make_secret(self, passwd, enc='SSHA'):
        salt = os.urandom(4)
        sha = hashlib.sha1(passwd)
        sha.update(salt)

        digest_salt_b64 = '{0}{1}'.format(
            sha.digest(), salt
        ).encode('base64').strip()
        tagged_digest_salt = '{{{0}}}{1}'.format(enc, digest_salt_b64)

        return tagged_digest_salt
