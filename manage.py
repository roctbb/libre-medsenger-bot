from flask import Flask
from models import db
from flask_script import Manager
from flask_migrate import Migrate
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from config import *

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FlaskIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

app = Flask(__name__)
db_string = "postgresql://{}:{}@{}:{}/{}".format(DB_LOGIN, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE)
app.config['SQLALCHEMY_DATABASE_URI'] = db_string

db.init_app(app)

migrate = Migrate(app, db)
