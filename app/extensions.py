# app/extensions.py
# extensions.py（プロジェクト直下 or utilsと同階層）
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
