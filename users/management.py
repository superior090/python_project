from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from database import Base, get_db
from users.auth import User, UserCreate, UserOut, UserUpdate, hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(tags=["Users"])


@router.post("/users/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password= user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/users/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)): #current_user: User = Depends(get_current_user)):
    return db.query(User).all()


@router.get("/users/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/me", response_model=UserOut)
def update_user(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.username:
        current_user.username = data.username
    if data.email:
        current_user.email = data.email
    if data.password:
        current_user.hashed_password = hash_password(data.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/users/me")
def delete_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.delete(current_user)
    db.commit()
    return {"message": "User deleted successfully"}
