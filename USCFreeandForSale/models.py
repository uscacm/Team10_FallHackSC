import datetime
from google.appengine.ext import db
from google.appengine.api import users


class Category(db.Model):
    name = db.StringProperty(required=True)
    priority_sort = db.IntegerProperty(required=True, default=0);
    created = db.DateProperty(auto_now_add=True)

class User(db.Model):
    fbid = db.StringProperty(required=True)
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    avatar_url = db.StringProperty(required=False)
    profile_link = db.StringProperty(required=False)
    created = db.DateProperty(auto_now_add=True)

class Item(db.Model):
    user = db.ReferenceProperty(User, collection_name='items')
    item_name = db.StringProperty(required=True)
    photo_url = db.StringProperty(required=False)
    category = db.ReferenceProperty(Category, collection_name='items')
    description = db.TextProperty(required=True)
    price = db.FloatProperty(required=False)
    data_source = db.IntegerProperty(required=True)
	#0 for user input , 1 from facebook group.
    sold_date = db.DateProperty(required=False)
    created = db.DateProperty(auto_now_add=True)
