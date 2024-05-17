from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi_pagination import Page, paginate, add_pagination
from fastapi_pagination.limit_offset import LimitOffsetPage, LimitOffsetParams
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, exc
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"  # Altere para sua URL do banco de dados

Base = declarative_base()

class Atleta(Base):
    __tablename__ = 'atletas'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    centro_treinamento = Column(String)
    categoria = Column(String)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/atletas/", response_model=Atleta)
def create_atleta(atleta: Atleta, db: Session = Depends(get_db)):
    db_atleta = db.query(Atleta).filter(Atleta.cpf == atleta.cpf).first()
    if db_atleta:
        raise HTTPException(status_code=303, detail=f"Já existe um atleta cadastrado com o cpf: {atleta.cpf}")
    try:
        db.add(atleta)
        db.commit()
        db.refresh(atleta)
        return atleta
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=303, detail=f"Já existe um atleta cadastrado com o cpf: {atleta.cpf}")

@app.get("/atletas/", response_model=Page[Atleta])
def read_atletas(db: Session = Depends(get_db), nome: str = None, cpf: str = None):
    query = db.query(Atleta)
    if nome:
        query = query.filter(Atleta.nome == nome)
    if cpf:
        query = query.filter(Atleta.cpf == cpf)
    return paginate(query.all())

@app.get("/atletas/limit-offset", response_model=LimitOffsetPage[Atleta])
def read_atletas_limit_offset(db: Session = Depends(get_db), params: LimitOffsetParams = Depends()):
    return paginate(db.query(Atleta).all(), params)

@app.get("/atletas/{atleta_id}", response_model=Atleta)
def read_atleta(atleta_id: int, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    if atleta is None:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")
    return atleta

add_pagination(app)
