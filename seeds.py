from app import create_app
from app.extensions import db
from app.models import User, Team, Category, Challenge, EventSettings

def seed_db():
    app = create_app()
    with app.app_context():
        print("Creating all tables in the database...")
        db.create_all()
        
        # Check if already seeded
        if User.query.first():
            print("Database already seeded!")
            return
            
        print("Creating Event Settings...")
        settings = EventSettings(event_name="XSSPloit CTF", is_live=True)
        db.session.add(settings)

        print("Creating admin user...")
        admin = User(username='admin', email='admin@xssploit.ctf', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        print("Creating default categories...")
        cat_web = Category(name='Web Exploitation', description='Web app vulnerabilities.')
        cat_crypto = Category(name='Cryptography', description='Break the cipher.')
        cat_pwn = Category(name='Pwn / Binary Exploitation', description='Memory corruption.')
        db.session.add_all([cat_web, cat_crypto, cat_pwn])
        db.session.commit()
        
        print("Creating demo challenges...")
        chal1 = Challenge(
            title='Inspector', slug='inspector', category_id=cat_web.id,
            difficulty='Easy', points=50, description='Can you inspect the element and find the flag?',
            is_visible=True
        )
        chal1.set_flag('XSS{1nsp3ct_th3_un3xp3ct3d}')
        
        chal2 = Challenge(
            title='Caesar Salad', slug='caesar-salad', category_id=cat_crypto.id,
            difficulty='Easy', points=100, description='I encrypted my flag with ROT13. Synt: KFF{ebg13_vf_abg_rapelcgvba}',
            is_visible=True
        )
        chal2.set_flag('XSS{rot13_is_not_encryption}')
        
        db.session.add_all([chal1, chal2])
        db.session.commit()
        
        print("Seeding complete! You can login with 'admin' / 'admin123'.")

if __name__ == '__main__':
    seed_db()
