from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="ArcFace Recognition API",
    description="A complete face recognition backend using DeepFace, ArcFace, and FastAPI.",
    version="1.0.0"
)

# Allow CORS for easy frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "running", "engine": "DeepFace (ArcFace)"}

if __name__ == "__main__":
    import uvicorn
    # Make sure to run this file directly or use `uvicorn main:app --reload`
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
