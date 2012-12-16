from tables import engine, feed_urls, feed_items
from sqlalchemy import insert, select, and_
from datetime import datetime
from time import mktime
import hashlib
import feedparser

def to_datetime(t):
    return datetime.fromtimestamp(mktime(t))

def update_feed(url):
    """ Updates the feed if it has been modified since it was last updated
        or if it's a new feed
    """
    now = datetime.now()
    d = feedparser.parse(url)
    if 'title' not in d.feed:
        print '{0} is probably not a feed'.format(url)
        return None

    if d.feed.get('modified_parsed'):
        feed_updated = to_datetime(d.feed.modified_parsed)
    elif d.feed.get('updated_parsed'):
        feed_updated = to_datetime(d.feed.updated_parsed)
    else:
        feed_updated = now

    conn = engine.connect()
    s = select([feed_urls], feed_urls.c.url == url)
    row = conn.execute(s).fetchone()

    if row == None:
        conn.execute(feed_urls.insert(), url=url, title=d.feed.title)
        row = conn.execute(s).fetchone()

    if row.updated < feed_updated:
        print 'Updating feed ' + url
        for entry in d.entries:
            add_feed_entry(row.id, entry, conn, now)
        u = feed_urls.update().where(feed_urls.c.id==row.id) \
                .values(title=d.feed.title, updated=now)
        conn.execute(u)
    conn.close()
    return row

def get_unique_id(entry, values):
    if 'guid' in entry:
        contents = entry['guid']
    elif 'id' in entry:
        contents = entry['id']
    elif 'contents' in values:
        contents = values['contents']
    elif 'summary' in values:
        contents = values['summary']
    md5 = hashlib.md5()
    md5.update(contents)
    return md5.hexdigest()

def add_feed_entry(feed_id, entry, conn, now):
    # Populate entry values
    values = { 'updated': now }

    for field in ['author', 'link', 'title']:
        if entry.get(field):
            values[field] = entry.get(field)

    if entry.get('published_parsed'):
        values['published'] = to_datetime(entry.published_parsed)

    if 'summary' in entry:
        values['summary'] = entry.summary
    elif 'description' in entry:
        values['summary'] = entry.description

    if 'content' in entry:
        values['contents'] = ''
        for content in entry.content:
            values['contents'] += content.value

    uid = get_unique_id(entry, values)

    # Update if already exists
    equal = and_(feed_items.c.feed_id==feed_id, feed_items.c.uid==uid)
    s = select([feed_items], equal)
    row = conn.execute(s).fetchone()
    if row:
        item_updated = now
        if entry.get('updated_parsed'):
            item_updated = to_datetime(entry.updated_parsed)
        elif entry.get('published_parsed'):
            item_updated = to_datetime(entry.published_parsed)

        if item_updated > row.updated:
            print '\n\nITEM UPDATED at {0} LAST VISITED at {1}' .format(item_updated, row.updated)
            u = feed_items.update().where(equal)
            conn.execute(u.values(values))
    else:
        conn.execute(feed_items.insert(), feed_id=feed_id, uid=uid, **values)

def get_feed(url):
    row = update_feed(url)
    if not row:
        return None

    conn = engine.connect()
    feed = {'feed': row}
    s = select([feed_items], feed_items.c.feed_id == row.id) \
            .order_by(feed_items.c.published.desc())
    feed['items'] = conn.execute(s).fetchall()
    conn.close()

    return feed

def get_feed_list():
    conn = engine.connect()
    rows = conn.execute(select([feed_urls])).fetchall()
    conn.close()
    return rows

def get_all_items():
    conn = engine.connect()
    s = select([feed_items]).order_by(feed_items.c.published.desc())
    items = conn.execute(s).fetchall()
    conn.close()
    return items

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print 'Usage update|get [url]+'
        sys.exit(1)

    action = sys.argv[1]
    urls = sys.argv[2:]
    if action == 'update':
        for url in urls:
            update_feed(url)
    elif action == 'get':
        for url in urls:
            items = get_feed_items(url)
            print '==='
            print url
            print '==='
            for item in items:
                print '\t', item.title, item.summary, item.uid
                print '---'

