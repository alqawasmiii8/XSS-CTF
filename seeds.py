from app import create_app
from app.extensions import db
from app.models import User, Team, Category, Challenge, EventSettings, Page

def seed_db():
    app = create_app()
    with app.app_context():
        print("Creating all tables in the database...")
        db.create_all()
        
        # Check if already seeded
        if not User.query.filter_by(username='admin').first():
            print("Creating admin user...")
            admin = User(username='admin', email='admin@xssploit.ctf', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
        else:
            print("Admin user already exists.")
            
        if not EventSettings.query.first():
            print("Creating Event Settings...")
            settings = EventSettings(event_name="XSSPloit CTF", is_live=True)
            db.session.add(settings)
        else:
            print("Event Settings already exist.")

        if not Category.query.first():
            print("Creating default categories...")
            cat_web = Category(name='Web Exploitation', description='Web app vulnerabilities.')
            cat_crypto = Category(name='Cryptography', description='Break the cipher.')
            cat_pwn = Category(name='Pwn / Binary Exploitation', description='Memory corruption.')
            db.session.add_all([cat_web, cat_crypto, cat_pwn])
            db.session.commit() # Commit to get IDs for challenges
        else:
            print("Categories already exist.")
            cat_web = Category.query.filter_by(name='Web Exploitation').first()
            cat_crypto = Category.query.filter_by(name='Cryptography').first()
        
        if not Page.query.first():
            print("Creating default pages...")
            rules_page = Page(
                title='Rules',
                slug='rules',
                content='<h3>Rules of Engagement</h3><ul><li>No automated scanners (Dirbuster, SQLmap, etc).</li><li>No DDoS or infrastructure attacks.</li><li>Be respectful to other players.</li></ul>'
            )
            faq_page = Page(
                title='FAQ',
                slug='faq',
                content='<h3>Frequently Asked Questions</h3><p>Q: How do I submit a flag?<br>A: Find the flag in the format XSS{...} and submit it in the challenge panel.</p>'
            )
            db.session.add_all([rules_page, faq_page])
        else:
            print("Pages already exist.")
        
        if not Challenge.query.first() and cat_web and cat_crypto:
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
        else:
            print("Challenges already exist or categories missing.")
        
        db.session.commit()
        print("Seeding complete!")

if __name__ == '__main__':
    seed_db()

