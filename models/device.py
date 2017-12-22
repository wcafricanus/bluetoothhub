from mongoengine import Document, StringField, ReferenceField

from models.user import User


class Device(Document):
    mac = StringField(primary_key=True)
    owner = ReferenceField(User)
