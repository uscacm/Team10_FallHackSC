import datetime
from google.appengine.ext import db
from google.appengine.api import users


class Category(db.Model):
    name = db.StringProperty(required=True)
    sort = db.IntegerProperty(required=True, default=0);
    created = db.DateProperty(auto_now_add=True)
    slug = db.StringProperty(required=True)
    visible = db.BooleanProperty()

def create_item(params):
    my_document = search.Document(
    # Setting the doc_id is optional. If omitted, the search service will create an identifier.
    doc_id = 'PA6-5000'
    fields=[
       search.TextField(name='customer', value='Joe Jackson'),
       search.HtmlField(name='comment', value='this is <em>marked up</em> text'),
       search.NumberField(name='number_of_visits', value=7), 
       search.DateField(name='last_visit', value=datetime.now()),
       search.DateField(name='birthday', value=datetime(year=1960, month=6, day=19)),
       search.GeoField(name='home_location', value=search.GeoPoint(37.619, -122.37))
       ])

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
