from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/name/{name}")
def get_name(name: str):
    return {"message": f"Hello {name}"}

@app.get("/lastname/{lastname}")
def get_lastname(lastname: str):
    return {"message": f"Hello {lastname}"}