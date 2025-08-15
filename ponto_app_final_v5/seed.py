# seed.py - cria usuário admin demo e inicializa DB
from src import app
from src.models import db, User
from passlib.hash import bcrypt

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@example.com').first():
        u = User(nome='Admin', email='admin@example.com', senha_hash=bcrypt.hash('admin123'), is_admin=True)
        db.session.add(u)
        db.session.commit()
    print("Seed concluído. Usuário admin@example.com / senha: admin123")
