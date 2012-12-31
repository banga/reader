from datetime import datetime
from time import mktime

def time_to_datetime(time):
    if not time:
        return None
    return datetime.fromtimestamp(mktime(time))


