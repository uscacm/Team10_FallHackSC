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

    fields = [
       search.TextField(name='name',        value=item.item_name),
       search.TextField(name='description', value=item.description),
       search.DateField(name='created',     value=datetime.datetime.now()),
    ]

    if item.category:
        fields.append(search.TextField(name='category', value=item.category.slug))
    if item.price:
        fields.append(search.NumberField(name='price', value=item.price))

    new_search_document = search.Document(
        doc_id = str(item.key().id()),
        fields = fields
    )
    index = search.Index(name='items_search')
    index.put(new_search_document)

class User(db.Model):
    fbid = db.StringProperty(required=True)
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    avatar_url = db.StringProperty(required=False)
    profile_link = db.StringProperty(required=False)
    created = db.DateProperty(auto_now_add=True)

class Item(db.Model):
    user = db.StringProperty(required=True)
    item_name = db.StringProperty(required=True)
    photo_url = db.StringProperty(required=False)
    category = db.ReferenceProperty(Category, collection_name='items')
    description = db.TextProperty(required=True)
    price = db.FloatProperty(required=False)
    data_source = db.IntegerProperty(required=True)
	#0 for user input , 1 from facebook group.
    sold_date = db.DateProperty(required=False)
    pickup_location = db.StringProperty(required=False)
    contact_method = db.StringProperty(required=False)
    created = db.DateProperty(auto_now_add=True)

class BuyRequest(db.Model):
    message = db.StringProperty(required=False)
    phone = db.StringProperty(required=False)
    from_user = db.StringProperty(required=True)
    item = db.ReferenceProperty(Item, required=True, collection_name='buy_requests')
    to_user = db.StringProperty(required=True)
    reqd = db.BooleanProperty(required=True, default=False)
    def get_from_user(self):
        return User.get_by_auth_id(from_user)
