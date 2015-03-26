#coding: utf-8
import logging
import sys
import time

from skim.configuration import elastic, INDEX


logger = logging.getLogger(__name__)

MAPPINGS = {
    'mappings': {
        'feed': {
            'properties': {
                'title': {
                    'type': 'string',
                    'analyzer': 'english',
                    'fields': {
                        'raw': {
                            'type':  'string',
                            'index': 'not_analyzed'
                        }
                    }
                },
                'etag': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'modified': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'categories': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'icon': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'image': {
                    'type': 'string',
                    'index': 'not_analyzed'
                }
            }
        },
        'entry': {
            'properties': {
                'title': {
                    'type': 'string',
                    'analyzer': 'english'
                },
                'text': {
                    'type': 'string',
                    'analyzer': 'english'
                },
                'feed': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'image': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'published': {
                    'type': 'date',
                    'format': 'dateOptionalTime'
                },
                'url': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'enclosures': {
                    'type': 'nested',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'index': 'not_analyzed'
                        },
                        'url': {
                            'type': 'string',
                            'index': 'not_analyzed'
                        }
                    }
                }
            }
        }
    }
}

def ensure():
    logger.info('Ensuring index %r', INDEX)
    es = elastic()
    time.sleep(1)
    es.indices.create(index=INDEX, ignore=400, body=MAPPINGS)
    ensure_mapping();

def ensure_mapping():
    es = elastic()
    time.sleep(1)
    for doc_type, mapping in MAPPINGS['mappings'].items():
        es.indices.put_mapping(index=INDEX, doc_type=doc_type, body=mapping)

def remove():
    es = elastic()
    time.sleep(1)
    es.indices.delete(index=INDEX, ignore=404)


if __name__ == '__main__':
    if sys.argv[1:] == ['recreate']:
        remove()
    ensure()
