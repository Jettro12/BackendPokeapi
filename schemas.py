from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class SearchBase(BaseModel):
    pokemon: str

class SearchCreate(SearchBase):
    pass

class Search(SearchBase):
    id: int
    date: datetime

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    searches: List[Search] = []

    class Config:
        orm_mode = True