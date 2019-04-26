# mavapa

[![PyPI version](https://badge.fury.io/py/mavapa.svg)](https://badge.fury.io/py/mavapa)

Accounts Management


# Dependencies
## Packages
* python-ldap
* MySQL-python
* requests
* pony
* flask

### Debian/Ubuntu

```
#~ sudo apt install build-essential libsasl2-dev ldap-utils 
                    libldap2-dev libmysqlclient-dev python-virtualenv
#~
```

# Deploy
```
#~ git clone https://github.com/sergiotocalini/mavapa
#~ cd mavapa
#~ pip install -r requirements.txt
#~ APP_SETTINGS=mavapa.config.Local python run.py
#~
```

## Gunicorn
...

## Virtualenv
```
#~ virtualenv /etc/gunicorn/venvs/mavapa
#~ source /etc/gunicorn/venvs/mavapa/bin/activate
#~ pip install -r requirements.txt
#~ deactivate
#~
```
