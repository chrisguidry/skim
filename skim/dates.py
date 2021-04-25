from datetime import datetime, timezone


def utcnow():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def from_iso(isostring):
    if '.' in isostring:
        return datetime.strptime(isostring, '%Y-%m-%dT%H:%M:%S.%f%z')
    else:
        return datetime.strptime(isostring, '%Y-%m-%dT%H:%M:%S%z')
