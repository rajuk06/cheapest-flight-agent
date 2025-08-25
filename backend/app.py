import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from agent import search_entry

load_dotenv()

class SearchQuery(BaseModel):
    origins: List[str]
    destinations: List[str]
    depart_date: str
    return_date: Optional[str] = None
    adults: int = 1
    days_flex: int = 0
    limit_per_route: int = 30

app = FastAPI(title="Cheapest Flight Agent")

allow = [o.strip() for o in os.getenv("CORS_ORIGINS","http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/search")
def search(q: SearchQuery):
    if not q.origins or not q.destinations:
        raise HTTPException(status_code=400, detail="origins and destinations required")
    res = search_entry(q.origins, q.destinations, q.depart_date, q.return_date, q.adults, q.limit_per_route)
    return {"results": res}
