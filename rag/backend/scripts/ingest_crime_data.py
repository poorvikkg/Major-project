import os
import pandas as pd
import uuid
import sys
import asyncio

# Adjust path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.chroma_service import chroma_service
from backend.services.mongo_service import mongo_service
from backend.services.embedding_service import embedding_service

async def ingest_csv(filepath: str):
    filename = os.path.basename(filepath)
    print(f"Processing {filename}...")
    try:
        df = pd.read_csv(filepath)
        # Handle different column namings across CSVs or simply dump as JSON string
        records = df.to_dict(orient="records")
        
        # 1. Insert into MongoDB
        # Add metadata
        for record in records:
            record["source_file"] = filename
            
        await mongo_service.insert_many("crime_records", records)
        
        # 2. Insert into ChromaDB
        # We need to convert each row into a readable text chunk
        # E.g., "In Year 2021, State Karnataka, Murder cases were 1200."
        texts = []
        ids = []
        metadatas = []
        
        for i, row in enumerate(records):
            # Create a simple representation of the row
            # Take the first few columns as context, up to 10
            items = []
            for k, v in list(row.items())[:10]:
                if pd.notna(v) and k != "source_file":
                    items.append(f"{k}: {v}")
            
            text_chunk = f"Record from {filename} -> " + ", ".join(items)
            
            texts.append(text_chunk)
            ids.append(f"{filename}_{i}_{uuid.uuid4().hex[:6]}")
            metadatas.append({"source": filename, "type": "statistic"})

        # Batch embed and insert
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            
            embeddings = embedding_service.embed_batch(batch_texts)
            chroma_service.add_to_collection(
                collection_name="crime_statistics",
                ids=batch_ids,
                embeddings=embeddings,
                metadatas=batch_metas,
                documents=batch_texts
            )
            print(f"  Inserted batch {i//batch_size + 1} into ChromaDB")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

async def main():
    archive_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "archive (4)")
    if not os.path.exists(archive_dir):
        print(f"Archive directory not found: {archive_dir}")
        return
        
    csv_files = [f for f in os.listdir(archive_dir) if f.endswith('.csv')]
    print(f"Found {len(csv_files)} CSV files to ingest.")
    
    # Just ingest a couple for testing to avoid huge runtime
    for f in csv_files[:2]: 
        await ingest_csv(os.path.join(archive_dir, f))
        
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(main())
