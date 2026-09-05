from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from context.service import get_area_comparison
from mangum import Mangum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/default/regrove_api")
def read_root():
    return {"message": "FastAPI backend is running"}


@app.get("/default/regrove_api/api/area/{postcode}")
def area_comparison(postcode: str):
    return get_area_comparison(postcode)


handler = Mangum(app)
