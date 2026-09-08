"""
api.py
FastAPI app entrypoint and REST routes.
Auth routes (signup/login) are implemented here for Phase 3.
Upload/chat/history routes get added in later phases.
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
import schemas
import auth
import upload as upload_module
import rag

# Creates tables if they don't already exist. Fine for an assignment;
# a real project would use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Intelligent Document Assistant")


@app.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserSignup, db: Session = Depends(get_db)):
    existing = (
        db.query(models.User)
        .filter(
            (models.User.username == payload.username)
            | (models.User.email == payload.email)
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/upload", response_model=schemas.DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Save the raw file to disk
    filepath = upload_module.save_upload_file(file, current_user.id)

    # 2. Extract its text (fails loudly here if the file is empty/unreadable,
    #    which is better than silently storing a document with no content)
    text = upload_module.extract_text(filepath)

    # 3. Record it in the DB first. vectorstore_path starts blank - we need
    #    doc.id to exist before we can namespace the FAISS index by it, so
    #    the row has to be committed before step 4 can run.
    doc = models.Document(
        filename=file.filename,
        filepath=filepath,
        vectorstore_path="",
        owner_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 4. Module 3 - RAG Pipeline: chunk the text, embed each chunk, and
    #    save a FAISS index to disk. If this fails, roll back the DB row
    #    too - we don't want a Document record pointing at an index that
    #    doesn't exist.
    try:
        vectorstore_path = rag.build_vectorstore(doc.id, text)
    except Exception as e:
        db.delete(doc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to build vector index: {e}")

    doc.vectorstore_path = vectorstore_path
    db.commit()
    db.refresh(doc)
    return doc


@app.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Document)
        .filter(models.Document.owner_id == current_user.id)
        .all()
    )
