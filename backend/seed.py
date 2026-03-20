from .database import SessionLocal
from .models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 5 fixed users — change passwords before going to production!
SEED_USERS = [
    {"username": "alice",   "password": "alice123"},
    {"username": "bob",     "password": "bob456"},
    {"username": "charlie", "password": "charlie789"},
    {"username": "diana",   "password": "diana321"},
    {"username": "eve",     "password": "eve654"},
]

def seed_users():
    db = SessionLocal()
    try:
        for u in SEED_USERS:
            exists = db.query(User).filter(User.username == u["username"]).first()
            if not exists:
                user = User(
                    username=u["username"],
                    hashed_password=pwd_context.hash(u["password"])
                )
                db.add(user)
        db.commit()
        print("[seed] Users seeded successfully.")
    except Exception as e:
        print(f"[seed] Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()
