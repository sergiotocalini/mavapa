title: mavapa

Mavapa is an Identity Provider. It allows you to integrated your OpenLDAP or Active Directory with an
OAuth service.

# Introducttion


# OpenLDAP

```
~$ cat schema.ldif
dn: ou=People,dc=example,dc=org
objectClass: organizationalUnit
ou: People

dn: ou=Groups,dc=example,dc=org
objectClass: organizationalUnit
ou: Groups

dn: ou=Apps,dc=example,dc=org
objectClass: organizationalUnit
ou: Apps

# Add John Smith to the organization
dn: uid=john.doe,ou=People,dc=example,dc=org
changetype: add
objectClass: inetOrgPerson
 description: John Doe from Accounting. John is the project
 manager of the building project, so contact him with any q
 uestions.
cn: John
sn: Doe
uid: john.doe
~$
```
