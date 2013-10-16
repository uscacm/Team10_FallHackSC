# -*- coding: utf-8 -*-
import logging
import secrets
import datetime

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
    if self.auth.get_user_by_session() is None: return None
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
    logging.info(self.current_user)
    values = {
      'url_for': self.uri_for,
      'logged_in': self.logged_in,
      'flashes': self.session.get_flashes(),
      'categories': self.category_list()
    }
    
    if self.logged_in:
       values['current_user'] = self.current_user

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
      recent_items = Item.all().order('-created').fetch(limit=10)
      popular_items = Item.all().order('created').fetch(limit=10)
      template_values = {'recent_items':recent_items,
                         'popular_items':popular_items}
      self.render('index.html', template_values)


class AddCategory(BaseRequestHandler):
  def get(self):
    if (Category.all().count() == 0):
      Category(name='Appliances', slug='appliances', visible=True).put()
      Category(name='Buy Requests', slug='buy', visible=True).put()
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
        self.session['next'] = '/sell'
        self.redirect('/auth/facebook') 		  
      else:
        template_values['categories'] = self.category_list()
        template_values['current_user'] = self.current_user
        self.render('newItem.html', template_values)



class BuyRequestPage(BaseRequestHandler):

    def get(self): 
        self.post()

    def post(self):
      template_values = {}
      if not self.logged_in:    
        self.session['next'] = '/buy'
        self.redirect('/auth/facebook')       
      else:
        template_values['current_user'] = self.current_user
        self.render('newBuyRequest.html', template_values)

class AddItemPage(BaseRequestHandler):
  def post(self):
    logging.info(self.request)
    template_values = {}
    if not self.logged_in:
      self.redirect('/auth/facebook')
    else: 
      new_item = Item(user=self.current_user.auth_ids[0],
                      item_name=self.request.get('item_name'), 
                      description=self.request.get('description'), 
                      data_source=0, # data source = from website
                      pickup_location=self.request.get('location'),
                      contact_method=self.request.get('contact'))
      if (self.request.get('file_url') != ' '):
        photo_url = self.request.get('file_url')
        new_item.photo_url = photo_url
      if (self.request.get('category') != 'CATEGORY'):
        category = Category.all().filter('slug = ', self.request.get('category')).get()
        new_item.category = category
      if (self.request.get('price').isdigit() ):
        new_item.price = float(self.request.get('price'))

      new_item.put()

      # Can comment out if broken
      AddItemSearchIndexes(new_item)

      template_values['current_user'] = self.current_user
      template_values['item'] = new_item
      self.render('ItemView.html', template_values)

class UpdateItem(BaseRequestHandler): 
  def post(self, item_id):
    template_values={}
    if not self.logged_in:
      self.redirect('auth/facebook')
    else:
      item = Item.get_by_id(int(item_id))
      item.item_name = self.request.get('item_name')
      item.description = self.request.get('description')
      item.pickup_location = self.request.get('pickup_location')
      item.contact_method = self.request.get('contact')
      if (self.request.get('file_url') != ' '):
        photo_url = self.request.get('file_url')
        item.photo_url = photo_url
      if (self.request.get('category') != 'CATEGORY'):
        category = Category.all().filter('name = ', self.request.get('category')).get()
        item.category = category
      if (self.request.get('price').isdigit() ):
        item.price = float(self.request.get('price'))
      item.put()
      AddItemSearchIndexes(item)

      self.redirect("/items")

class DeleteItem(BaseRequestHandler):
  def post(self, item_id):
    template_values={}
    if not self.logged_in:
      self.redirect('/auth/facebook')
    else: 
      item = Item.get_by_id(int(item_id))
      items_index = search.Index(name='items_search')
      items_index.delete(item.key().id())
      db.delete(item.key())
      # session flash?
      self.redirect("/items")

class MarkAsSold(BaseRequestHandler):
  def post(self, item_id):
    if not self.logged_in:
      self.redirect('/auth/facebook')
    else:
      item = Item.get_by_id(int(item_id))
      items_index = search.Index(name='items_search')
      item.sold_date = datetime.datetime.now()
      item.put()
      items_index.delete(item.key().id())
      # session flash?
      self.redirect('/items')



class BrowsePage(BaseRequestHandler):

  def get(self): 
      self.post()

  def post(self):
    ITEMS_PER_PAGE = 50
    if self.request.get('page'):
      page = int(self.request.get('page'))
    else: page = 1
    page -= 1 # offset for the first page
    page *= ITEMS_PER_PAGE

    items = Item.all().order('-created').filter('sold_date = ', None).fetch(limit=ITEMS_PER_PAGE, offset=page)
    template_values = {'items':items}
    self.render('items_list.html', template_values)
       

class BuyRequestHandler(BaseRequestHandler):
  def post(self):
    if not self.current_user:
      self.redirect('/auth/facebook')
      return

    item = Item.get_by_id(long(self.request.get('item_id')))
    if not item:
      self.abort(404)
      return

    user = self.current_user
    buy_req = BuyRequest(
        message   = self.request.get('message'),
        phone     = self.request.get('phone'),
        from_user = self.current_user.auth_ids[0],
        to_user   = item.user,
        item      = item)

    buy_req.put()
    self.render('request_successful.html', {'buy_request': buy_req, 'item': item, 'to_user': self.auth.store.user_model.get_by_auth_id(item.user)})

    #class BuyRequest(db.Model):
    #description = db.StringProperty(required=False)
    #phone = db.StringProperty(required=False)
    #from_user = db.StringProperty(required=True)
    #item = db.ReferenceProperty(Item, required=True, collection_name='buy_requests')
    #to_user = db.StringProperty(required=True)

class SearchHandler(BaseRequestHandler):

  def get(self): 
      self.post()

  def post(self):
    ###
    ### https://www.google.com/events/io/2011/sessions/full-text-search.html
    ### Need to insert items into the index when they get inserted into the db, update them aswell
    ###
      try:
        query = self.request.get('q')
        term = self.request.get('q')
        if not query:
          query = ' '
          term = ' (anything) '
        items_index = search.Index(name='items_search')
        if self.request.get('cat') and len(self.request.get('cat')) > 0:
          search_results = items_index.search(query + ' AND category:"'+self.request.get('cat')+'"')
        else:
          #search_results = items_index.search(query)
          search_results = items_index.search(query)
        getter_ids = []
        for result in search_results.results:
          getter_ids.append(long(result.doc_id))
        items = Item.get_by_id(getter_ids)
        template_values = {"results": search_results.results, "term": term, "cat": self.request.get('cat'), "items": items}
        self.render('search_results.html', template_values)
      except search.Error:
        logging.error('err!')
        self.abort(500)

class BrowseCategoryPage(BaseRequestHandler):
  def post(self, cat_slug):
    self.get()

  def get(self, cat_slug):
      logging.error(cat_slug)
      category = Category.all().filter('slug = ', cat_slug).get()
      if not category:
        self.abort(404)
      else:
        template_values = {'category': category, 'items': category.items.order('-created').filter('sold_date = ', None).fetch(50)}
        return self.render('category.html', template_values)

class ItemPage(BaseRequestHandler):

  def get(self, item_id):
      self.post(item_id)

  def post(self, item_id): 
    item = Item.get_by_id(int(item_id))
    template_values = {'item': item}
    self.render('ItemView.html', template_values)


class ItemListPage(BaseRequestHandler):

  def get(self):
    self.post()

  def post(self):
    if not self.current_user:
      self.redirect('/auth/facebook')
      return
      
    items = Item.all().filter('user = ', self.current_user.auth_ids[0]).fetch(40)
    buy_requests = BuyRequest.all().filter('to_user = ', self.current_user.auth_ids[0]).fetch(40)
    for buy_request in buy_requests:
      buy_request.from_user_obj = self.auth.store.user_model.get_by_auth_id(buy_request.from_user)
      
    template_values = {'items': items, 'buy_requests': buy_requests}
    self.render('my_items.html', template_values)


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
    #self.redirect('/profile')
    self.redirect('/')

  
  def _on_signin__old(self, data, auth_info, provider):
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

    logging.info(**data)

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

    if self.session['next']:
      self.redirect(self.session['next'])
    else:
      # Go to the profile page
      self.redirect('/')

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



