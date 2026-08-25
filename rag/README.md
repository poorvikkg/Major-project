# Police Case Intelligence Assistant (PCIA)

An AI-powered conversational assistant that enables police officers to retrieve case information, discover crime patterns, identify related cases, and analyze uploaded FIR documents using Retrieval-Augmented Generation (RAG).

## Prerequisites
- **Python 3.11** or higher (Stable versions recommended)
- **Node.js** (v18+)
- **MongoDB** running locally on `localhost:27017`
- A **Groq API Key** (for the LLM)

---

## 0. Initial Setup
Before running the servers, you must set up your environment variables:
1. Navigate to the `backend` folder.
2. Copy `.env.example` to a new file named `.env`.
3. Open `.env` and paste your actual `GROQ_API_KEY`.

---

## 1. Start the Backend API

Open a new PowerShell terminal in the project root directory (`RAG/`) and run:

```powershell
# Activate the virtual environment
.\backend\venv\Scripts\activate

# Set the Python Path so imports resolve correctly
$env:PYTHONPATH="."

# Start the FastAPI Server
uvicorn backend.main:app --port 8000 --reload
```
*The backend API will now be listening on `http://localhost:8000`*

---

## 2. Start the Frontend UI

Open a **second** new PowerShell terminal in the project root directory (`RAG/`) and run:

```powershell
# Navigate to the frontend directory
cd frontend

# Install dependencies (only needed the first time)
npm install

# Start the Vite development server
npm run dev
```
*The UI will now be available in your browser at `http://localhost:5173`*

---

## 3. Data Ingestion (Crucial First Time Setup)
Because the vector database (`chroma_db`) and raw datasets are too large to host on GitHub, **you must generate the database yourself** before the AI can answer any questions.

1. Create a folder named `archive (4)` in the root directory.
2. Download your crime statistics CSVs and place them inside `archive (4)`.
3. Run the ingestion script to read the CSVs and build your local `chroma_db`:

```powershell
# Open a terminal in the root directory
.\backend\venv\Scripts\activate
$env:PYTHONPATH="."

# Run the ingestion script
python backend/scripts/ingest_crime_data.py
```
*This will take a few minutes. Once it completes, your ChromaDB is ready and you can start asking the AI questions!*
