import sys
# inject './lib' dir in the path so that we can simply do "import ndb" 
# or whatever there's in the app lib dir.
if 'lib' not in sys.path:
    sys.path[0:0] = ['lib']

import os, urllib
import webapp2
from webapp2 import Route
import jinja2
import secrets
import handlers

# webapp2 config
app_config = {
  'webapp2_extras.sessions': {
    'cookie_name': '_simpleauth_sess',
    'secret_key': secrets.SESSION_KEY
  },
  'webapp2_extras.auth': {
    'user_attributes': []
  }
}

application = webapp2.WSGIApplication([

    # app routes
    Route('/',        'handlers.MainPage',     name="home"),
    Route('/sell',    'handlers.SellPage',     name="sell"),
    Route('/additem', 'handlers.AddItemPage',  name="additem"),
    Route('/browse',  'handlers.BrowsePage',   name="browse"),
    Route('/items',   'handlers.ItemListPage', name='items'),

    Route(r'/item/<item_id:\d+>', 'handlers.ItemPage',     name='item'),
    Route('/category/<cat_slug>', 'handlers.BrowseCategoryPage', name='browse_category'),
    Route('/search', 'handlers.SearchHandler', name='search'),

    Route('/admin/category/add', 'handlers.AddCategory'),


    # auth routes
    Route('/profile',
            handler='handlers.ProfileHandler',             name='profile'),
    Route('/logout',
            handler='handlers.AuthHandler:logout',         name='logout'),
    Route('/auth/<provider>',
            handler='handlers.AuthHandler:_simple_auth',   name='auth_login'),
    Route('/auth/<provider>/callback', 
            handler='handlers.AuthHandler:_auth_callback', name='auth_callback')

], config=app_config, debug=True)


