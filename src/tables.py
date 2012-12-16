from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, UnicodeText, MetaData, ForeignKey, UniqueConstraint
from datetime import datetime

engine = create_engine('mysql://root@localhost/feedme', echo=True)

metadata = MetaData()

feed_urls = Table('feed_urls', metadata,
        Column('id', Integer, primary_key=True),
        Column('url', String(500), nullable=False),
        Column('title', UnicodeText),
        Column('updated', DateTime, default=datetime(1960,1,1)))

feed_items = Table('feed_items', metadata,
        Column('id', Integer, primary_key=True),
        Column('feed_id', None, ForeignKey('feed_urls.id')),
        Column('uid', String(32), nullable=False),
        Column('link', UnicodeText),
        Column('author', UnicodeText),
        Column('title', UnicodeText),
        Column('summary', UnicodeText),
        Column('contents', UnicodeText),
        Column('updated', DateTime, default=datetime(1960,1,1)),
        Column('published', DateTime),
        UniqueConstraint('feed_id', 'uid'))

metadata.create_all(engine)
