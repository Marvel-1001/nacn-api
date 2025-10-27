# from sqlalchemy.orm import Session
# from models import User
# from db import SessionLocal
# from passlib.context import CryptContext

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def create_admin():
#     db: Session = SessionLocal()
#     try:
#         if not db.query(User).first():
#             admin = User(
#                 email="admin@example.com",
#                 hashed_password=pwd_context.hash("admin1"),
#                 is_active=True
#             )
#             db.add(admin)
#             db.commit()
#             print("✅ Admin created.")
#         else:
#             print("ℹ️ Admin already exists.")
#     finally:
#         db.close()