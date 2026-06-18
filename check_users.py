from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print('Total users:', len(users))
    for u in users:
        print(f'{u.id}: {u.name} ({u.email}) - {u.role}')
