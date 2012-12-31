""" Feed.py

    Methods that deal with fetching, reading and writing feeds
"""
from tables import feeds, stories, with_connection, on_duplicate_update
from sqlalchemy import select, and_
from fetcher import update_feed


@with_connection
def get_feed_list(connection):
    return connection.execute(select([feeds])).fetchall()


@with_connection
def get_all_stories(page=1, page_size=25, connection=None):
    s = select([stories, feeds], from_obj=[stories.join(feeds)]) \
        .order_by(stories.c.published.desc()).apply_labels() \
        .limit(page_size).offset((page-1)*page_size)
    return connection.execute(s).fetchall()


@with_connection
def get_feed(url, connection):
    """ Loads a feed's metadata
    """
    return connection.execute(select([feeds], feeds.c.url == url)).fetchone()


@with_connection
def get_feed_stories(feed_id, connection):
    """ Loads the stories stored for a feed
    """
    s = select([stories], stories.c.feed_id == feed_id) \
          .order_by(stories.c.published.desc())
    return connection.execute(s).fetchall()


@with_connection
def write_feed(row, stories, connection):
    """ Update the feed if it has been modified since it was last updated
        or if it's a new feed
    """
    s = select([feeds], feeds.c.url == row['url'])
    old_row = connection.execute(s).fetchone()

    if old_row is None:
        connection.execute(feeds.insert(), **row)
        old_row = connection.execute(s).fetchone()

    if old_row.fetched < row['updated']:
        print 'Updating feed ' + row['url']

        for story in stories.itervalues():
            story['feed_id'] = old_row.id
            write_story(story, connection)

        u = feeds.update().where(feeds.c.id == old_row.id).values(**row)
        connection.execute(u)
        return True

    return False


def write_story(story, connection):
    on_duplicate_update(
        connection,
        stories,
        and_(stories.c.feed_id == story['feed_id'],
             stories.c.uid == story['uid']),
        story)


def main():
    import sys

    if len(sys.argv) < 3:
        print 'Usage update|get [url]+'
        sys.exit(1)

    action = sys.argv[1]
    urls = sys.argv[2:]
    if action == 'update':
        urls_updated = 0
        for url in urls:
            feed = get_feed(url)
            updated_feed = update_feed(url, feed)
            if updated_feed and write_feed(*updated_feed):
                urls_updated += 1
        print '{0} feeds updated'.format(urls_updated)
    elif action == 'get':
        for url in urls:
            feed = get_feed(url)
            print '==='
            print url
            print '==='
            for story in get_feed_stories(feed.id):
                print '\t', story.title, story.summary, story.uid
                print '---'


if __name__ == "__main__":
    main()
