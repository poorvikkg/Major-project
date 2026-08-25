from backend.services.chroma_service import chroma_service
from backend.services.mongo_service import mongo_service
from backend.services.embedding_service import embedding_service
from backend.services.llm_service import llm_service
from backend.models.schemas import ChatResponse
import json
import re

class HybridRetriever:
    async def chat(self, query: str, session_id: str = None) -> ChatResponse:
        # 1. Intent Classification / Query Understanding (Could use a small LLM call, but doing heuristics or single LLM prompt)
        intent_prompt = f"""
        Classify the intent of the following user query for a Police Intelligence Assistant.
        Query: "{query}"
        Respond with ONLY ONE of the following categories:
        - CASE_SEARCH: Searching for specific cases, persons, or FIRs.
        - STATISTICS: Asking for trends, rates, or statistical data.
        - GENERAL: General police procedure or unrelated question.
        """
        # For a full implementation, we might use Groq here.
        # To save tokens/time, we'll assume everything is a hybrid search for now.
        
        # 2. Vector Search (ChromaDB)
        query_emb = embedding_service.embed_text(query)
        
        # Search crime statistics
        stats_results = chroma_service.search_collection("crime_statistics", query_emb, n_results=3)
        # Search FIR documents (if any)
        fir_results = chroma_service.search_collection("fir_documents", query_emb, n_results=3)
        
        # 3. Structured Search (MongoDB)
        # In a real scenario, we'd extract entities like "Mysore" or "Murder" to query Mongo.
        # We'll just fetch a few recent cases for context.
        recent_cases = await mongo_service.search_cases({}, limit=2)
        
        # 4. Context Building
        context_chunks = []
        sources = set()
        
        if stats_results and stats_results['documents'] and len(stats_results['documents'][0]) > 0:
            for i, doc in enumerate(stats_results['documents'][0]):
                context_chunks.append(doc)
                if stats_results['metadatas'][0][i] and 'source' in stats_results['metadatas'][0][i]:
                    sources.add(stats_results['metadatas'][0][i]['source'])
                    
        if fir_results and fir_results['documents'] and len(fir_results['documents'][0]) > 0:
             for i, doc in enumerate(fir_results['documents'][0]):
                context_chunks.append(doc)
                if fir_results['metadatas'][0][i] and 'source' in fir_results['metadatas'][0][i]:
                    sources.add(fir_results['metadatas'][0][i]['source'])
        
        context_str = "\n---\n".join(context_chunks)
        
        # 5. LLM Prompt
        system_prompt = """
        You are a highly capable AI Investigation Assistant for police officers.
        Answer the user's query using ONLY the provided context. 
        If the context is insufficient, say "I don't have enough information in the indexed data to answer that."
        Never invent case IDs, statistics, or IPC sections.
        Your output should be authoritative, clear, and professional.
        """
        
        final_prompt = f"Context:\n{context_str}\n\nUser Query: {query}"
        
        # 6. Generate Answer
        answer = await llm_service.generate_response(final_prompt, system_prompt)
        
        # 7. Confidence & Related formatting
        confidence = 0.95 if context_chunks else 0.40
        if "I don't have enough information" in answer:
            confidence = 0.10
            
        return ChatResponse(
            answer=answer,
            confidence=confidence,
            sources=list(sources),
            supporting_cases=[],
            related_cases=[],
            suggested_follow_ups=["Can you provide more specific details?", "Show similar cases in other districts."]
        )

# Singleton
hybrid_retriever = HybridRetriever()
