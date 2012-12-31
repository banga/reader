""" Fetcher.py

    Handles fetching feed stories and saving them
"""
import feedparser
import hashlib

from datetime import datetime
from tables import engine, feeds
from util import time_to_datetime


def update_feed(url, row_proxy):
    """ Fetches new stories for the feed at :url: and returns (feed, stories)
    """
    row = {'fetched': datetime.now()}

    if row_proxy:
        parsed = feedparser.parse(url, etag=row_proxy.etag,
                             modified=row_proxy.modified)
        for column in row_proxy.keys():
            row[column] = row_proxy[column]
    else:
        parsed = feedparser.parse(url)

    # version is empty when the url is not a feed or when we give
    # modified/etag values and the feed hasn't changed
    if not parsed.version:
        print '{0} is not a feed or hasn\'t changed'.format(url)
        return None

    if parsed.status == 400:
        print '{0} has been permanently shut down'.format(url)
        return None

    if parsed.status == 301:
        print '{0} moved permanently to {1}'.format(url, parsed.url)
        conn = engine.connect()
        conn.execute(feeds.update().where(feeds.c.url == url)
                     .values(url=parsed.url))
        conn.close()
        url = parsed.url

    row['url'] = url
    row['title'] = parsed.feed.get('title', row.get('title'))
    row['etag'] = unicode(parsed.get('etag'))
    row['modified'] = unicode(parsed.get('modified'))

    parsed_time = parsed.feed.get('modified_parsed',
                                  parsed.feed.get('updated_parsed'))
    row['updated'] = time_to_datetime(parsed_time) or row['fetched']

    story_rows = {}
    for entry in parsed.entries:
        story_row = _make_story_row(row['fetched'], entry)
        story_rows[story_row['uid']] = story_row

    return (row, story_rows)


def _make_story_row(fetched, entry):
    story = {'fetched': fetched}

    story['author'] = entry.get('author')
    story['link'] = entry.get('link')
    story['title'] = entry.get('title')
    story['published'] = time_to_datetime(entry.get('published_parsed'))
    story['summary'] = entry.get('summary', entry.get('description'))
    story['published'] = time_to_datetime(
        entry.get('updated_parsed',
                  entry.get('published_parsed'))) or fetched
    story['contents'] = ''

    #TODO: parse the content better, esp. the base urls
    for content in entry.get('content', []):
        story['contents'] += content.value

    story['uid'] = _make_story_uid(entry, story)
    return story


def _make_story_uid(entry, story):
    md5 = hashlib.md5()
    md5.update(entry.get('guid')
               or entry.get('id')
               or story['contents']
               or story['summary'])
    return md5.hexdigest()

