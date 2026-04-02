from flask import Flask
from routes.user_routes import user_bp
from routes.aisug_routes import aisug
from extensions import db
from dotenv import load_dotenv

load_dotenv()

app=Flask(__name__)
app.config.from_object("config.Config")

#Initialize db
db.init_app(app)

with app.app_context():
    db.create_all()

# Register routes
@app.route('/')
def hello():
    return "Testing at opening"

app.register_blueprint(user_bp,url_prefix="/api/users")
app.register_blueprint(aisug,url_prefix="/api/ai")