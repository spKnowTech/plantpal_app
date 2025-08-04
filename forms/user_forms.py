from fastapi import Form
from pydantic import EmailStr

class UserCreateForm:
    """Form for user registration."""
    def __init__(
        self,
        full_name: str = Form(...),
        email: EmailStr = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        location: str = Form(...)
    ):
        self.full_name: str = full_name
        self.email: EmailStr = email
        self.password: str = password
        self.confirm_password: str = confirm_password
        self.location: str = location

class UserLoginForm:
    """Form for user login."""
    def __init__(
        self,
        email: EmailStr = Form(...),
        password: str = Form(...)
    ):
        self.email: EmailStr = email
        self.password: str = password