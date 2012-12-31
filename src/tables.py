from sqlalchemy import create_engine, select, Table, Column, Integer, String, DateTime, UnicodeText, MetaData, ForeignKey, UniqueConstraint
from datetime import datetime

engine = create_engine('mysql://root@localhost/feedme', echo=False)

metadata = MetaData()

feeds = Table('feeds', metadata,
        Column('id', Integer, primary_key=True),
        Column('url', String(500), nullable=False),
        Column('title', UnicodeText),
        Column('updated', DateTime),
        Column('fetched', DateTime, default=datetime(1960,1,1)),
        Column('etag', UnicodeText),
        Column('modified', UnicodeText))

stories = Table('stories', metadata,
        Column('id', Integer, primary_key=True),
        Column('feed_id', None, ForeignKey('feeds.id')),
        Column('uid', String(32), nullable=False),
        Column('link', UnicodeText),
        Column('author', UnicodeText),
        Column('title', UnicodeText),
        Column('summary', UnicodeText),
        Column('contents', UnicodeText),
        Column('fetched', DateTime, default=datetime(1960,1,1)),
        Column('published', DateTime),
        UniqueConstraint('feed_id', 'uid'))

metadata.create_all(engine)

def with_connection(fn, *args, **kwargs):
    ''' A decorator to provide a connection from the engine
        Useful for shorter functions and using pools in the future
    '''
    def wrapped(*args, **kwargs):
        conn = engine.connect()
        result = fn(*args, connection=conn, **kwargs)
        conn.close()
        return result
    return wrapped

def on_duplicate_update(conn, table, equality, values):
    ''' If the row specified by |equality| exists in |table|,
        update it with |values|, otherwise insert it with |values|
    '''
    row = conn.execute(select([table], equality)).fetchone()
    if row:
        conn.execute(table.update().where(equality).values(values))
    else:
        conn.execute(table.insert(), **values)
