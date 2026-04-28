from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/name/{name}")
def get_name(name: str):
    return {"message": f"Hello {name}"}


@app.get("/fullname/{name}/{lastname}")
def get_fullname(name: str, lastname: str):
    return {"message": f"Hello {name} {lastname}"}

@app.get("/age/{age}")
def get_age(age: int):
    return {"message": f"You are {age} years old"}