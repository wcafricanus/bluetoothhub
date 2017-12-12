from mongoengine import Document, StringField


class User(Document):
    email = StringField(primary_key=True)
    password = StringField()

    def __init__(self, email, password, *args, **values):
        super().__init__(*args, **values)
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.email)

