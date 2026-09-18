from fastapi import FastAPI

app = FastAPI(title="ShelterHub API")


@app.get("/health")
def health():
    return {"status": "ok"}
