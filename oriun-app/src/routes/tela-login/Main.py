from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class LoginData(BaseModel):
    email: str
    password: str

@app.post("/login")
def login(data: LoginData):
    if data.email == "benedito@oriun.com" and data.password == "123456":
        return {"token": "fake-jwt-token"}
    return {"error": "Credenciais inválidas"}
