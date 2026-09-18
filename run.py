from app import create_app
from app.models import db
from app.services.categorizer import seed_default_categories

app = create_app()

with app.app_context():
    db.create_all()
    seed_default_categories()

if __name__ == '__main__':
    app.run(debug=True)