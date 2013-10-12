import os
import urllib
import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions = ['jinja2.ext.autoescape'])


class MainPage(webapp2.RequestHandler):
    def get(self): 
        self.post()

    def post(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('views/index.html')
        self.response.write(template.render(template_values))


class SellPage(webapp2.RequestHandler):
    def get(self): 
        self.post()

    def post(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('views/newItem.html')
        self.response.write(template.render(template_values))

class BrowsePage(webapp2.RequestHandler):
    def get(self): 
        self.post()

    def post(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('views/items_list.html')
        self.response.write(template.render(template_values))

class MyItemPage(webapp2.RequestHandler):
    def get(self): 
        self.post()

    def post(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('views/myItems.html')
        self.response.write(template.render(template_values))

class ItemsPage(webapp2.RequestHandler):
    def get(self): 
        self.post()

    def post(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('views/item_view.html')
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sell', SellPage),
    ('/browse', BrowsePage),
    ('/item', MyItemPage),
    ('/items', ItemsPage)
], debug=True)
