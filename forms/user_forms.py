from fastapi import Form
from pydantic import EmailStr

class UserCreateForm:
    def __init__(
        self,
        full_name: str = Form(...),
        email: EmailStr = Form(...),
        password: str = Form(...),
        location: str = Form(...)
    ):
        self.full_name = full_name
        self.email = email
        self.password = password
        self.location = location


class UserLoginForm:
    def __init__(
            self,
            email: str = Form(...),
            password: str = Form(...),
    ):
        self.email = email
        self.password = password
