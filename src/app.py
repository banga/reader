import feed
import tornado.ioloop
from tornado.web import Application, RequestHandler, URLSpec

class MainHandler(RequestHandler):
    def get(self, page=1):
        page = int(page)
        html = ''
        if page > 1:
            html += '<a href="{0}">Previous</a>'.format(
                    self.reverse_url('main', page-1))
        html += '<a href="{0}">Next</a><br/>'.format(
                self.reverse_url('main', page+1))

        for story in feed.get_all_stories(page):
            if story.stories_title:
                html += u'<a href="{0}"><b>{1}</b></a> - <a href="{3}">{2}</a><br/>' \
                        .format(story.stories_link or '#',
                                story.stories_title,
                                story.feeds_title,
                                self.reverse_url('fetch', story.feeds_url))
            if story.stories_author:
                html += u'by {0}<br/>'.format(story.stories_author)
            if story.stories_published:
                html += u'{0}<br/>' \
                        .format(story.stories_published.strftime('%b %d %Y'))
        self.write(html)

class FetchFeedHandler(RequestHandler):
    def get(self, url):
        f = feed.get_feed(url)
        if f:
            story_rows = feed.get_feed_stories(f.id)
            html = u'<h1>{title}</h1>Updated: {updated}<hr/>' \
                    .format(**f)
            for row in story_rows:
                if 'title' in row:
                    html += u'<a href="{1}"><b>{0}</b></a>' \
                            .format(row['title'], row['link'])
                if 'published' in row and row.published:
                    html += u' {0}<br/>' \
                            .format(row['published'].strftime('%c'))
                html += '<br/>'
                if 'contents' in row and row.contents:
                    html += u'{0}<br/><hr/>'.format(row['contents'])
                elif 'summary' in row:
                    html += u'{0}<br/><hr/>'.format(row.summary)
            self.write(html)
        else:
            self.write('Feed not found')

class ListFeedsHandler(RequestHandler):
    def get(self):
        html = u''
        for f in feed.get_feed_list():
            html += u'<a href={0}>{1}</a><br/>' \
                    .format(self.reverse_url('fetch', f.url), f.title)
        self.write(html)

if __name__ == "__main__":
    app = Application([
        URLSpec(r"/([1-9][0-9]*)", MainHandler, name='main'),
        URLSpec(r"/f/(.*)", FetchFeedHandler, name='fetch'),
        URLSpec(r"/l/", ListFeedsHandler, name='list'),
    ], debug=True)
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
