from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import ChatRequest, ChatResponse, UploadResponse, CompareRequest, CompareResponse
from backend.services.retrieval import hybrid_retriever
from backend.utils.document_processor import document_processor
from backend.services.chroma_service import chroma_service
from backend.services.embedding_service import embedding_service
from backend.services.llm_service import llm_service
import shutil
import os
import uuid

app = FastAPI(title="Police Case Intelligence Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await hybrid_retriever.chat(request.query, request.session_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_file_in_background(temp_path: str, filename: str, collection_id: str):
    try:
        # Extract text and chunk
        chunks = document_processor.process_pdf(temp_path, filename)
        
        if not chunks:
            return
            
        texts = [c['text'] for c in chunks]
        ids = [c['id'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]
        
        embeddings = embedding_service.embed_batch(texts)
        
        chroma_service.add_to_collection(
            collection_name=collection_id,
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
    except Exception as e:
        print(f"Background processing error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/upload", response_model=UploadResponse)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Save temp file
    temp_path = f"temp_{uuid.uuid4().hex[:8]}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create unique collection ID
    collection_id = f"upload_{uuid.uuid4().hex[:8]}"
    
    # Offload the heavy work
    background_tasks.add_task(process_file_in_background, temp_path, file.filename, collection_id)
    
    return UploadResponse(
        filename=file.filename, 
        status="success", 
        message="Document is being processed in the background.",
        collection_id=collection_id
    )

@app.post("/compare", response_model=CompareResponse)
async def compare_document(request: CompareRequest):
    # Just a mock response for now, to fully implement we would:
    # 1. Fetch chunks from request.collection_id
    # 2. Search against 'fir_documents' or 'crime_statistics'
    # 3. LLM comparison
    return CompareResponse(
        answer="Based on the analysis, this FIR shows a 94% similarity in modus operandi to Case 192, specifically regarding the method of entry.",
        similar_cases=[{"case_id": "192", "similarity": "94%", "reason": "Same modus operandi"}]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
