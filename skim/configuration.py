#coding: utf-8
import configparser
import os

parser = configparser.ConfigParser()
parser.read('skim.ini')
config = parser['skim']

APPLICATION_ROOT = config.get('application_root') or None
SECRET_KEY = config['secret_key']
STORAGE_ROOT = os.path.abspath(os.path.expanduser(config['storage_root']))

DEBUG = os.environ.get('ENV') == 'development'
ASSETS_DEBUG = DEBUG

import logging.config
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(processName)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'urllib3': {
            'handlers': ['default'],
            'level': 'WARN',
            'propagate': False
        },
        'MARKDOWN': {
            'handlers': ['default'],
            'level': 'WARN',
            'propagate': False
        }
    }
})
