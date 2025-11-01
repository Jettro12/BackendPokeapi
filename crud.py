from sqlalchemy.orm import Session
from models import User, Search
from schemas import UserCreate, SearchCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_search(db: Session, user_id: int, search: SearchCreate):
    db_search = Search(pokemon=search.pokemon, user_id=user_id)
    db.add(db_search)
    db.commit()
    db.refresh(db_search)
    return db_search

def get_searches_by_user(db: Session, user_id: int):
    return db.query(Search).filter(Search.user_id == user_id).order_by(Search.date.desc()).limit(10).all()