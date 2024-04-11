from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import time

from turkish_project_llm import extract_text_with_coordinates

from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
origins = [
    "http://localhost:4200",
    "http://localhost:3000",
    'https://lssfrontend.vercel.app/'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(MyMiddleware)

@app.post("/process_book/")
async def get_response(file):     
    responses = extract_text_with_coordinates(file)
    return {"response": responses}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)