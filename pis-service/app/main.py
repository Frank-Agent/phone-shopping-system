from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.routes import products, search, offers, reviews
from app.config import settings

app = FastAPI(title="Product Information Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(offers.router, prefix="/api/v1/offers", tags=["offers"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "PIS", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)