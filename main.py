from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "гитхаб работает - ура"}

if __name__ == "__main__":
    print("гитхаб работает - ура версия 2") 