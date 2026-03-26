from models.user_model import User
from extensions import db

def get_all_user():
    users=User.query.all()
    return [user.to_dict() for user in users]

def create_user(data):
    user=User(name=data["name"],email=data["email"])
    db.session.add(user)
    db.session.commit()
    return user.to_dict()