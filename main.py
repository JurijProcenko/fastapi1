import re
from datetime import date, datetime, timedelta
import time
from typing import Optional
import pathlib
from fastapi import (
    FastAPI,
    Path,
    Query,
    Depends,
    HTTPException,
    status,
    Request,
    File,
    UploadFile,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, EmailStr, validator
from sqlalchemy.sql import text
from sqlalchemy.orm import Session

from db import get_db, Contact

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


class ContactModel(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    lastname: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=12, max_length=20)
    born_date: date
    description: Optional[str] = Field(None, max_length=250)

    @validator("phone")
    def phone_number_must_have_12_digits(cls, phone):
        match = re.match(r"^\+?\d{2,3}\(?\d{2,3}\)?\s?(\d{2,3}\-?){2}\d{2,3}", phone)
        if match is None:
            raise ValueError("Phone number must have more than 12 digits")
        return phone


# Get full list of contacts
class ResponseContactModel(BaseModel):
    id: int = Field(default=1, ge=1)
    name: str = Field(min_length=3, max_length=50)
    lastname: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=13, max_length=20)
    born_date: date
    description: Optional[str] = Field(max_length=250)

    # class Config:
    #     orm_more = True


# Create a new contact
@app.post("/contacts")
async def create_new_contact(contact: ContactModel, db: Session = Depends(get_db)):
    new_contact = Contact(
        name=contact.name,
        lastname=contact.lastname,
        email=contact.email,
        phone=contact.phone,
        born_date=contact.born_date,
        description=contact.description,
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact


@app.get("/contacts")
async def get_all_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()

    return contacts


# Get one contact with the specific ID
@app.get("/contacts/{contact_id}")
async def read_contact(
    contact_id: int = Path(description="The ID of the contsct to get", gt=0),
    db: Session = Depends(get_db),
) -> ResponseContactModel:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


# Update exist contact
@app.patch("/contacts/{contact_id}")
async def update_contact(
    contact_id: int = Path(description="The ID of the contsct to get", gt=0),
    db: Session = Depends(get_db),
    name: str = None,
    lastname: str = None,
    email: EmailStr = None,
    phone: str = None,
    born_date: str = None,
    description: str = None,
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if name:
        contact.name = name
    if lastname:
        contact.lastname = lastname
    if email:
        contact.email = email
    if phone:
        contact.phone = phone
    if born_date:
        contact.born_date = born_date
    if description:
        contact.description = description
    new_contact = Contact(
        name=contact.name,
        lastname=contact.lastname,
        email=contact.email,
        phone=contact.phone,
        born_date=contact.born_date,
        description=contact.description,
    )

    db.commit()
    # db.refresh(contact)

    return {"message": "record was succefully updated"}


# Delete contact
@app.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: int = Path(description="The ID of the contsct to get", gt=0),
    db: Session = Depends(get_db),
):
    item = db.query(Contact).filter(Contact.id == contact_id).first()
    db.delete(item)
    db.commit()

    return {"message": "Item Deleted Succesfully"}


# Search for an email, name or lastname
@app.get("/search")
async def search_contact(
    db: Session = Depends(get_db),
    name: str = None,
    lastname: str = None,
    email: EmailStr = None,
):
    if name:
        return db.query(Contact).filter(Contact.name == name).first()
    if lastname:
        return db.query(Contact).filter(Contact.lastname == lastname).first()
    if email:
        return db.query(Contact).filter(Contact.email == email).first()

    return {"message": "Not Found"}


@app.get("/birthday")
async def get_birthday_week(db: Session = Depends(get_db)):
    users = db.query(Contact).all()
    week = date.today() + timedelta(days=6)
    happy_users = []
    for user in users:
        bday = datetime(
            date.today().year,
            user.born_date.month,
            user.born_date.day,
        ).date()

        if date.today() <= bday <= week:
            happy_users.append(user)

    return happy_users


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Invalid input data", "error": exc.json},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "error": exc.json},
    )


@app.exception_handler(Exception)
def unexpected_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred", "error": exc.__dict__},
    )


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print("!!!!!!  ", e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
