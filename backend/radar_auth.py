
import sqlite3
import time
import json
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuration
DB_FILE = "radar_data.db"
SECRET_KEY = "smart-edit-core-secret-key-change-this-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 * 30  # 30 days

# Security
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "viewer"  # admin, editor, viewer
    status: int = 1       # 1=active, 0=disabled

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    role: str

# Database Init
def init_auth_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username VARCHAR(50) PRIMARY KEY,
                  email VARCHAR(100),
                  hashed_password VARCHAR(255),
                  role VARCHAR(20) DEFAULT 'viewer',
                  status INTEGER DEFAULT 1,
                  created_at REAL)''')
    
    # Check if admin exists, if not create default
    c.execute("SELECT username FROM users WHERE username='admin'")
    if not c.fetchone():
        # Default admin: admin / admin123
        hashed = pwd_context.hash("admin123")
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", 
                  ("admin", "admin@example.com", hashed, "admin", 1, time.time()))
        print("Initialized default admin user.")
        
    conn.commit()
    conn.close()

init_auth_db()

# Operations
def get_user(username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, email, hashed_password, role, status FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return UserInDB(username=row[0], email=row[1], hashed_password=row[2], role=row[3], status=row[4])
    return None

def create_user(user: User, password: str):
    if get_user(user.username):
        return False, "User already exists"
    
    hashed = pwd_context.hash(password)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", 
                  (user.username, user.email, hashed, user.role, 1, time.time()))
        conn.commit()
        return True, "Success"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def list_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, email, role, status, created_at FROM users")
    res = []
    for r in c.fetchall():
        res.append({
            "username": r[0],
            "email": r[1],
            "role": r[2],
            "status": r[3],
            "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r[4]))
        })
    conn.close()
    return res

def update_user_role(username: str, role: str, status_code: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET role=?, status=? WHERE username=?", (role, status_code, username))
    conn.commit()
    conn.close()
    return True

def delete_user(username: str):
    if username == "admin": return False # Protect super admin
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()
    return True

# Auth Helper
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
        
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.status == 0:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
