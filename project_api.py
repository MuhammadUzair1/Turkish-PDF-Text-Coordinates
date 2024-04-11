from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests
import time

from turkish_project_llm import extract_text_from_pdf

from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

class PDFRequest(BaseModel):
    url: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(MyMiddleware)

@app.post("/process_book")
async def process_book(pdf_request: PDFRequest):
    pdf_url = pdf_request.url
    try:
        # Fetching PDF content from the URL
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_content = response.content

        # Processing PDF content to extract text coordinates
        text_coordinates = extract_text_from_pdf(pdf_content)

        return {"text_coordinates": text_coordinates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)