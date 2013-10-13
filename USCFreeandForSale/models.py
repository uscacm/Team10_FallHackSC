import datetime
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import search 

class Category(db.Model):
    name = db.StringProperty(required=True)
    sort = db.IntegerProperty(required=True, default=0);
    created = db.DateProperty(auto_now_add=True)
    slug = db.StringProperty(required=True)
    visible = db.BooleanProperty()

def AddItemSearchIndexes(item):
    
    return

    fields = [
       search.TextField(name='name', value=item.item_name),
       search.TextField(name='description', value=item.description)
    ]

    # Setting the doc_id is optional. If omitted, the search service will create an identifier.
    if item.category:
        fields.append(search.TextField(name='category', value=item.category.slug))
    if item.price:
        fields.append(search.NumberField(name='price', value=item.price))

    new_search_document = search.Document(
        doc_id = item.key,
        fields = fields
    )
    new_search_document.put()


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
    pickup_location = db.StringProperty(required=False)
    contact_method = db.StringProperty(required=True)
    created = db.DateProperty(auto_now_add=True)
