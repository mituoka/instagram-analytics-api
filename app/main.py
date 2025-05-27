from fastapi import FastAPI

app = FastAPI(
    title="Instagram Analytics API",
    description="Instagram influencer data analysis API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Instagram Analytics API!"}
