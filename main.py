from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import requests
from jose import jwt, JWTError
from datetime import datetime, timedelta
import time
import os
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, get_db
import crud, schemas, models

# ========================
# 🔐 JWT CONFIGURATION
# ========================
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ========================
# 🚀 APPLICATION SETUP
# ========================
app = FastAPI(title="PokeAPI Backend - FastAPI + PostgreSQL + Docker")

# CORS - AGREGAR TU DOMINIO DE NETLIFY EXPLÍCITAMENTE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pokeaapp.netlify.app",  # Tu frontend en Netlify
        "http://localhost:3000",         # Desarrollo local
        "http://localhost:8000",         # Desarrollo local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# 🕒 WAIT FOR DATABASE
# ========================
def wait_for_db():
    max_retries = 15
    retry_interval = 3

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                print("✅ Database connection successful")
            # Forzar creación de tablas
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("✅ Tables created successfully")
            return
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}/{max_retries}: Error - {str(e)}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print("❌ Could not connect to database")
                print("⚠️ Continuing without database...")

# ========================
# 🔑 JWT FUNCTIONS
# ========================
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ========================
# 🏠 ENDPOINTS
# ========================
@app.get("/")
def read_root():
    return {
        "message": "✅ PokeAPI Backend running correctly",
        "docs": "/docs",
        "frontend": "https://pokeaapp.netlify.app"
    }

# ========================
# 👤 USER REGISTRATION
# ========================
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_username(db, user.username)
        if db_user:
            raise HTTPException(status_code=400, detail="User already registered")
        return crud.create_user(db, user)
    except Exception as e:
        print(f"❌ Error in /register: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# 🔐 LOGIN
# ========================
@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_username(db, user.username)
        if not db_user or not crud.verify_password(user.password, db_user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect credentials")
        token = create_access_token({"sub": db_user.username})
        
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        print(f"❌ Error in /login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# 🔍 QUERY POKÉMON (via PokeAPI)
# ========================
@app.get("/pokemon/{name}")
def get_pokemon(name: str, db: Session = Depends(get_db)):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
        res = requests.get(url)

        if res.status_code != 200:
            raise HTTPException(status_code=404, detail="Pokémon not found")

        data = res.json()
        pokemon_info = {
            "name": data["name"],
            "sprite": data["sprites"]["front_default"],
            "height": data["height"],
            "weight": data["weight"],
            "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        }

        return pokemon_info
    except Exception as e:
        print(f"❌ Error in /pokemon: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
   

   @app.get("/debug/tables")
def debug_tables(db: Session = Depends(get_db)):
    try:
        # Listar todas las tablas y columnas
        result = db.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)
        columns = [{"table": row[0], "column": row[1], "type": row[2]} for row in result]
        return {"columns": columns}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/recreate-tables")
def debug_recreate_tables():
    try:
        # Forzar recreación de tablas
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return {"message": "✅ Tables recreated successfully"}
    except Exception as e:
        return {"error": str(e)}
# ========================
# 🧠 LOCAL EXECUTION
# ========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)