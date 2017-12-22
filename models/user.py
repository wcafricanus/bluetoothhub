from mongoengine import Document, StringField


class User(Document):
    email = StringField(primary_key=True)
    password = StringField()
    display_name = StringField()

    def __init__(self, email, password, display_name, *args, **values):
        super().__init__(*args, **values)
        self.email = email
        self.password = password
        self.display_name = display_name

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

