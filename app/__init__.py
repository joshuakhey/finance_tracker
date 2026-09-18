from flask import Flask
import os


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
        'sqlite:////mnt/JHardDrive/data/jheypicloud/files/Finances/fintrack.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from .models import db
    db.init_app(app)

    with app.app_context():
        from .routes.dashboard import dashboard_bp
        from .routes.transactions import transactions_bp
        from .routes.investments import investments_bp
        from .routes.sync import sync_bp

        app.register_blueprint(dashboard_bp)
        app.register_blueprint(transactions_bp)
        app.register_blueprint(investments_bp)
        app.register_blueprint(sync_bp)

    return app