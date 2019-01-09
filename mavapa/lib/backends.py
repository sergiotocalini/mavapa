#!/usr/bin/env python
import os
import hashlib
import ldap
from anytree import Node
from anytree.exporter import DictExporter

class LDAP():
    def __init__(self, **kwargs):
        # Loading defaults connection options
        kwargs.setdefault('host', 'localhost')
        kwargs.setdefault('port', 389)
        kwargs.setdefault('binddn', '')
        kwargs.setdefault('bindpw', '')
        self.copt = kwargs.copy()
        # Connect with the defaults options
        self.connect()
        
    def connect(self, **kwargs):
        self.copt.update(kwargs)
        try:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            self.cstr = ldap.initialize(self.copt['host'])
	    self.cstr.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
	    self.cstr.set_option(ldap.OPT_REFERRALS, 0)
	    self.cstr.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
	    self.cstr.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
	    self.cstr.set_option( ldap.OPT_X_TLS_DEMAND, True )
	    self.cstr.set_option( ldap.OPT_DEBUG_LEVEL, 255 )
            if all(map(lambda x: self.copt[x] != '', ['binddn', 'bindpw'])):
                self.cstr.simple_bind_s(self.copt['binddn'], self.copt['bindpw'])
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
                    entries = (x[0].replace(',%s' %(kwargs['basedn']), '')).split(',')
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
                        node = Node(e, parent=parent, dn=','.join([e, parent.dn]))
                    parent = node
        return exporter.export(root)

    def query(self, **kwargs):
        kwargs.setdefault('basedn', '')
        kwargs.setdefault('filter', '(objectclass=person)')
        kwargs.setdefault('attrs', ['*'])
        kwargs.setdefault('scope', ldap.SCOPE_SUBTREE)
        kwargs.setdefault('limit', 25)
        kwargs.setdefault('dn', False)
        try:
            rows = []
            if not kwargs['dn']:
                res = self.cstr.search(kwargs['basedn'], kwargs['scope'],
                                       kwargs['filter'], kwargs['attrs'])
                while 1:
                    rtype, rdata = self.cstr.result(res, 0)
                    if (rdata == []):
                        break
                    else:
                        if rtype == ldap.RES_SEARCH_ENTRY:
                            [rows.append(i) for i in rdata]
            else:
                res = self.cstr.search_s(kwargs['filter'], kwargs['scope'])
                for idx in res:
                    rows.append(idx)
            return rows
        except ldap.LDAPError:
            print(ldap.LDAPError)
            return False
        except Exception as e:
            print(str(e))
            return False

    def modify(self, dn, new_dict, old_dict={}):
        tasks = []
        for i in new_dict:
            if old_dict.has_key(i):
                if old_dict[i] == '*':
                    tasks.append((ldap.MOD_REPLACE, i, new_dict[i]))
                else:
                    tasks.append((ldap.MOD_DELETE, i, old_dict[i]))
                    tasks.append((ldap.MOD_ADD, i, new_dict[i]))
            else:
                tasks.append((ldap.MOD_ADD, i, new_dict[i]))

        print(dn, tasks)
        self.cstr.modify_s(dn, tasks)
        
    def make_secret(self, passwd, enc='SSHA'):
        salt = os.urandom(4)
        sha = hashlib.sha1(passwd)
        sha.update(salt)

        digest_salt_b64 = '{0}{1}'.format(sha.digest(), salt).encode('base64').strip()
        tagged_digest_salt = '{{{0}}}{1}'.format(enc, digest_salt_b64)
        
        return tagged_digest_salt
