import feedparser
from flask import Flask, url_for
import feed

app = Flask(__name__)

@app.route("/g/<path:url>")
def get_feed(url):
    f = feed.get_feed(url)
    if f:
        html = u'<h1>{title}</h1>Updated: {updated}<hr/>' \
                .format(**f['feed'])
        for item in f['items']:
            if item.title:
                html += u'<a href="{1}"><h2>{0}</h2></a>'.format(item.title, item.link)
            if item.published:
                html += u'Posted on {0}<br/>'.format(item.published.strftime('%c'))
            if item.contents:
                html += u'{0}<br/><hr/>'.format(item.contents)
            elif item.summary:
                html += u'{0}<br/><hr/>'.format(item.summary)
        return html
    return 'Feed not found'

@app.route("/l/")
def list_feeds():
    html = u''
    for f in feed.get_feed_list():
        html += u"<a href={0}>{1}</a><br/>".format(url_for('get_feed', url=f.url), f.title)
    return html

@app.route("/")
def get_latest_items():
    html = ''
    for item in feed.get_all_items():
        if item.title:
            html += u'<a href="{0}"><h3>{1}</h3></a>'.format(item.link or '#', item.title)
        if item.author:
            html += u'by {0}<br/>'.format(item.author)
        if item.published:
            html += u'{0}<br/>'.format(item.published.strftime('%b %d %Y'))
    return html

if __name__ == '__main__':
    app.run(debug=True)
