# -*- coding: utf-8 -*-
import logging
import secrets

import webapp2
from google.appengine.api import search 

import facebook
import json
from google.appengine.api import memcache
from google.appengine.ext import db

from webapp2_extras import auth, sessions, jinja2
from jinja2.runtime import TemplateNotFound
from models import *

from simpleauth import SimpleAuthHandler



class BaseRequestHandler(webapp2.RequestHandler):
  def dispatch(self):
    # Get a session store for this request.
    self.session_store = sessions.get_store(request=self.request)
    
    try:
      # Dispatch the request.
      webapp2.RequestHandler.dispatch(self)
    finally:
      # Save all sessions.
      self.session_store.save_sessions(self.response)
  
  @webapp2.cached_property    
  def jinja2(self):
    """Returns a Jinja2 renderer cached in the app registry"""
    return jinja2.get_jinja2(app=self.app)
    
  @webapp2.cached_property
  def session(self):
    """Returns a session using the default cookie key"""
    return self.session_store.get_session()
    
  @webapp2.cached_property
  def auth(self):
      return auth.get_auth()
  
  @webapp2.cached_property
  def current_user(self):
    """ Returns currently logged in user """
    user_dict = self.auth.get_user_by_session()
    return self.auth.store.user_model.get_by_id(user_dict['user_id'])
      
  @webapp2.cached_property
  def logged_in(self):
    """ Returns true if a user is currently logged in, false otherwise """
    return self.auth.get_user_by_session() is not None
  
  def category_list(self):
    categories = memcache.get('categories')
    if categories is not None:
        return categories 
    else:
       categories = Category.all().order('sort')
       if not memcache.set('categories', categories):
         logging.error('Memcache set failed.')
       return categories
      
  def render(self, template_name, template_vars={}):
    # Preset values for the template
    values = {
      'url_for': self.uri_for,
      'logged_in': self.logged_in,
      'flashes': self.session.get_flashes(),
      'categories': self.category_list()
    }
    
    # Add manually supplied template values
    values.update(template_vars)
    
    # read the template or 404.html
    try:
      self.response.write(self.jinja2.render_template(template_name, **values))
    except TemplateNotFound:
      self.response.write('can\'t find yo template')
      #self.abort(404)

  def head(self, *args):
    """Head is used by Twitter. If not there the tweet button shows 0"""
    pass


class MainPage(BaseRequestHandler):
  def get(self): 
      self.post()

  def post(self):
      logging.info(self.request)
      template_values = {}
      self.render('index.html', template_values)


class AddCategory(BaseRequestHandler):
  def get(self):
    if (Category.all().count() == 0):
      Category(name='Appliances', slug='appliances', visible=True).put()
      Category(name='Furniture', slug='furniture', visible=True).put()
      Category(name='Clothing', slug='clothing', visible=True).put()
      Category(name='Tickets', slug='tickets', visible=True).put()
      Category(name='Books', slug='books', visible=True).put()
      Category(name='Electronics', slug='electronics', visible=True).put()
      Category(name='Transportation', slug='transportation', visible=True).put()
      Category(name='Housing', slug='housing', visible=True).put()
      Category(name='Misc', slug='misc', visible=True).put()
        


class SellPage(BaseRequestHandler):

    def get(self): 
        self.post()

    def post(self):
        template_values = {}
        if not self.logged_in:
          self.redirect('/auth/facebook')
        else:
          template_values['current_user'] = self.current_user
          self.render('newItem.html', template_values)

class AddItemPage(BaseRequestHandler):
  def post(self):
    template_values = {}
    if not self.logged_in:
      self.redirect('/auth/facebook')
    else: 
      new_item = Item(item_name=self.request.get('item_name'), 
                      description=self.request.get('description'), 
                      data_source=0,
                      pickup_location=self.request.get('location'),
                      contact_method=self.request.get('contact'))
      if (self.request.get('category') != 'CATEGORY'):
        category = Category.all().filter('name =', self.request.get('category')).get()
        # category = Category.gql("WHERE name='%s'" % self.request.get('category'))
        new_item.category = category;
      if (self.request.get('price').isdigit() ):
		    new_item.price =  float(self.request.get('price'))
      new_item.put()
      template_values['current_user'] = self.current_user
      template_values['item'] = new_item
      self.render('ItemView.html', template_values)

class BrowsePage(BaseRequestHandler):

  def get(self): 
      self.post()

  def post(self):
      template_values = {'items':Item.all()}
      self.render('items_list.html', template_values)
       
class SearchHandler(BaseRequestHandler):

  def get(self): 
      self.post()

  def post(self):
    ###
    ### https://www.google.com/events/io/2011/sessions/full-text-search.html
    ### Need to insert items into the index when they get inserted into the db, update them aswell
    ###
      if not self.request.get('q'):
        self.abort(404)
        return

      try:
        items_index = search.Index(name='items_search')
        if self.request.get('cat'):
          search_results = index.search('title:"' + query + '" AND desc:"' + query + '" AND category:"'+self.request.get('cat')+'"')
        else:
          search_results = index.search('title:"' + query + '" AND desc:"' + query + '"')
        template_values = {results: search_results}
        self.render('search_results.html', template_values)
        return
      except search.Error:
        logging.error('err!')
        self.abort(500)

class BrowseCategoryPage(BaseRequestHandler):
  def post(self, cat_slug):
    self.get()

  def get(self, cat_slug):
      logging.error('k')
      category = Category.all().filter('slug = ', cat_slug).get()
      if not category:
        self.abort(404)
        template_values = {category: category, items: category.items.all()}
        return self.render('category.html', template_values)

class ItemPage(BaseRequestHandler):

  def get(self, item_id):
      self.post(item_id)

  def post(self, item_id): 
    item = Item.get(item_id)
    template_values = {'item': item}
    self.render('ItemView.html', template_values)


class ItemListPage(BaseRequestHandler):

  def get(self):
    self.post()

  def post(self):
    template_values = {}
    self.render('myItems.html', template_values)


class RootHandler(BaseRequestHandler):

  def get(self):
    """Handles default langing page"""
    self.render('home.html')
    
class ProfileHandler(BaseRequestHandler):

  def get(self):
    """Handles GET /profile"""    
    if self.logged_in:
      self.render('profile.html', {
        'user': self.current_user, 
        'session': self.auth.get_user_by_session()
      })
    else:
      self.redirect('/')


class AuthHandler(BaseRequestHandler, SimpleAuthHandler):
  """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

  # Enable optional OAuth 2.0 CSRF guard
  OAUTH2_CSRF_STATE = True
  
  USER_ATTRS = {
    'facebook' : {
      'id'     : lambda id: ('avatar_url', 
        'http://graph.facebook.com/{0}/picture?type=large'.format(id)),
      'name'   : 'name',
      'link'   : 'link'
    },
    'google'   : {
      'picture': 'avatar_url',
      'name'   : 'name',
      'profile': 'link'
    }
  }
  
  def _on_signin(self, data, auth_info, provider):
    """Callback whenever a new or existing user is logging in.
     data is a user info dictionary.
     auth_info contains access token or oauth token and secret.
    """

    # Possible flow:
    # 
    # 1. check whether user exist, e.g.
    #    User.get_by_auth_id(auth_id)
    #
    # 2. create a new user if it doesn't
    #    User(**data).put()
    #
    # 3. sign in the user
    #    self.session['_user_id'] = auth_id
    #
    # 4. redirect somewhere, e.g. self.redirect('/profile')
    #
    # See more on how to work the above steps here:
    # http://webapp-improved.appspot.com/api/webapp2_extras/auth.html
    # http://code.google.com/p/webapp-improved/issues/detail?id=20


    auth_id = '%s:%s' % (provider, data['id'])
    logging.info('Looking for a user with id %s', auth_id)
    
    user = self.auth.store.user_model.get_by_auth_id(auth_id)
    _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

    if user:
      logging.info('Found existing user to log in')
      # Existing users might've changed their profile data so we update our
      # local model anyway. This might result in quite inefficient usage
      # of the Datastore, but we do this anyway for demo purposes.
      #
      # In a real app you could compare _attrs with user's properties fetched
      # from the datastore and update local user in case something's changed.
      user.populate(**_attrs)
      user.put()
      self.auth.set_session(
        self.auth.store.user_to_dict(user))
      
    else:
      # check whether there's a user currently logged in
      # then, create a new user if nobody's signed in, 
      # otherwise add this auth_id to currently logged in user.

      if self.logged_in:
        logging.info('Updating currently logged in user')
        
        u = self.current_user
        u.populate(**_attrs)
        # The following will also do u.put(). Though, in a real app
        # you might want to check the result, which is
        # (boolean, info) tuple where boolean == True indicates success
        # See webapp2_extras.appengine.auth.models.User for details.
        u.add_auth_id(auth_id)
        
      else:
        logging.info('Creating a brand new user')
        ok, user = self.auth.store.user_model.create_user(auth_id, **_attrs)
        if ok:
          self.auth.set_session(self.auth.store.user_to_dict(user))

    # Remember auth data during redirect, just for this demo. You wouldn't
    # normally do this.
    self.session.add_flash(data, 'data - from _on_signin(...)')
    self.session.add_flash(auth_info, 'auth_info - from _on_signin(...)')

    # Go to the profile page
    self.redirect('/profile')

  def logout(self):
    self.auth.unset_session()
    self.redirect('/')

  def handle_exception(self, exception, debug):
    logging.error(exception)
    self.render('error.html', {'exception': exception})
    
  def _callback_uri_for(self, provider):
    return self.uri_for('auth_callback', provider=provider, _full=True)
    
  def _get_consumer_info_for(self, provider):
    """Returns a tuple (key, secret) for auth init requests."""
    return secrets.AUTH_CONFIG[provider]
    
  def _to_user_model_attrs(self, data, attrs_map):
    """Get the needed information from the provider dataset."""
    user_attrs = {}
    for k, v in attrs_map.iteritems():
      attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
      user_attrs.setdefault(*attr)

    return user_attrs



