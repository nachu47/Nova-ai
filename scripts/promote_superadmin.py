#!/usr/bin/env python3
import sys
import os

# Add backend directory to sys.path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from app.database.session import SessionLocal
from app.models.entities import User

def promote_superadmin(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email '{email}' not found.")
            sys.exit(1)
        
        print(f"User found: {user.full_name} ({user.email})")
        print(f"Current role: {user.role}")
        
        if user.role == "superadmin":
            print("User is already a superadmin.")
            sys.exit(0)
            
        confirm = input(f"Are you sure you want to promote {user.email} to superadmin? (yes/no): ")
        if confirm.lower() != "yes":
            print("Operation cancelled.")
            sys.exit(0)
            
        user.role = "superadmin"
        db.commit()
        print(f"Successfully promoted {user.email} to superadmin.")
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_superadmin.py <email>")
        sys.exit(1)
        
    promote_superadmin(sys.argv[1])
