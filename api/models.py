from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

class Student(BaseModel):
    mssv: str
    name: str
    gender: str
    dob: str
    major: str
    class_name: str
