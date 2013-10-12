import os
import urllib
import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader = jinja2.FileSystemLoader(os.path.dirname(__file__) + '/views'),
  extensions = ['jinja2.ext.autoescape'])


class MainPage(webapp2.RequestHandler):

    def get(self): 
        self.post();

    def post(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))



application = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
