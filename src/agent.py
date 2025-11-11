import os
import json
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict
import hashlib
from dotenv import load_dotenv

class Agent:
    def __init__(self, openrouter_api_key: str, model: str = "alibaba/tongyi-deepresearch-30b-a3b:free", load_embedding = False): # "google/gemini-flash-1.5-8b"):
        """
        Initialize RAG system with offline embeddings and OpenRouter LLM
        
        Args:
            openrouter_api_key: Your OpenRouter API key
            model: OpenRouter model to use (default: gemini-flash-1.5-8b)
        """
        self.use_rag = load_embedding # if we do not load embedding, we definitely don't use RAG
        if load_embedding:
            # Initialize offline embedding model
            print("Loading offline embedding model...")
            self.embedding_model = SentenceTransformer('./models/all-MiniLM-L6-v2')  # Lightweight local model
            
            # Initialize ChromaDB for vector storage
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")

            # Try to get existing collection, create if doesn't exist
            try:
                self.collection = self.chroma_client.get_collection("rag_documents")
            except:
                self.collection = self.chroma_client.create_collection("rag_documents")
        
        # OpenRouter configuration
        self.openrouter_api_key = openrouter_api_key
        self.model = model
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.context = None # global context
        
        # Store conversation history
        self.conversation_history = []
    
    def add_documents(self, documents, metadata = None):
        """
        Add documents to the vector database
        
        Args:
            documents: List of text documents
            metadata: Optional list of metadata dictionaries
        """
        # if metadata is None:
        #     metadata = [{} for _ in documents]
        
        # Generate embeddings offline
        print("Generating embeddings...")
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Generate document IDs
        doc_ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadata,
            ids=doc_ids
        )
        
        print(f"Added {len(documents)} documents to the database")
    
    def search_similar_documents(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search for similar documents using offline embeddings
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        # Generate query embedding offline
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        similar_docs = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                similar_docs.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return similar_docs
    
    def call_openrouter(self, messages: List[Dict]) -> str:
        """
        Call OpenRouter API
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated response text
        """
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 10000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            print("Timeout")
            return 'Timeout'
        except Exception as e:
            print(f"Error calling OpenRouter: {e}")
            return f"Error: {str(e)}"
    
    def generate_response(self, query: str, use_rag: bool = False, add_response_to_history: bool = True) -> str:
        """
        Generate response using RAG + LLM
        
        Args:
            query: User query
            use_rag: Whether to use RAG or just LLM
            
        Returns:
            Generated response
        """
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        if use_rag and self.use_rag: # embedding must be loaded

            context = self.context
            if context is None:
                # Search for relevant documents
                similar_docs = self.search_similar_documents(query)
                if similar_docs:
                    for i, doc in enumerate(similar_docs, 1):
                        context += f"{doc['content']}\n"

            if not context is None:
                # Create system message with context
                system_message = {
                    "role": "system",
                    "content": f"""Here is the context knowledge maybe you can take into account. 
                    If the context doesn't contain relevant information, use your general knowledge.
                    
                    {context}
                    """
                }
                # Prepare messages for LLM
                messages = [system_message] + self.conversation_history #self.conversation_history[-6:]  # Keep last 6 messages for context
                # print(f'Context: {context}')
            else:
                messages = self.conversation_history
        else:
            messages = self.conversation_history
        
        
        # Generate response
        response = self.call_openrouter(messages)
        
        # Add assistant response to conversation history
        if add_response_to_history:
            self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []

# Example usage and test data
def create_sample_documents():
    """Create sample documents for testing"""
    documents = [
        "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
        "Deep learning uses neural networks with multiple layers to process complex patterns in data.",
        "Natural Language Processing (NLP) focuses on enabling computers to understand and process human language.",
        "Python is a popular programming language for machine learning and data science due to its simplicity and extensive libraries.",
        "TensorFlow and PyTorch are the two most popular deep learning frameworks used by researchers and practitioners.",
        "The transformer architecture, introduced in 2017, revolutionized natural language processing tasks.",
        "Reinforcement learning involves training agents through rewards and punishments in an environment.",
        "Computer vision enables machines to interpret and understand visual information from the world.",
        "Large Language Models (LLMs) like GPT are trained on vast amounts of text data and can generate human-like text.",
        "Retrieval-Augmented Generation (RAG) combines retrieval systems with language models for more accurate responses."
    ]
    
    metadata = [
        {"topic": "machine learning", "type": "definition"},
        {"topic": "deep learning", "type": "definition"},
        {"topic": "NLP", "type": "definition"},
        {"topic": "programming", "type": "tool"},
        {"topic": "frameworks", "type": "tool"},
        {"topic": "NLP", "type": "architecture"},
        {"topic": "reinforcement learning", "type": "method"},
        {"topic": "computer vision", "type": "field"},
        {"topic": "LLMs", "type": "model"},
        {"topic": "RAG", "type": "technique"}
    ]
    
    return documents, metadata

def main():
    # Initialize RAG system
    load_dotenv()
    
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    if OPENROUTER_API_KEY is None:
        print("API Key isn't found.")
        exit(0)
    
    rag_system = Agent(openrouter_api_key=OPENROUTER_API_KEY, load_embedding=True)
    
    # Add sample documents
    documents, metadata = create_sample_documents()
    rag_system.add_documents(documents, metadata)
    
    print("RAG System Ready! Type 'quit' to exit, 'clear' to clear history, 'rag off' to disable RAG")
    print("-" * 50)
    
    use_rag = True
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'clear':
            rag_system.clear_conversation_history()
            print("Conversation history cleared.")
            continue
        elif user_input.lower() == 'rag off':
            use_rag = False
            print("RAG disabled - using LLM only")
            continue
        elif user_input.lower() == 'rag on':
            use_rag = True
            print("RAG enabled")
            continue
        
        # Generate response
        response = rag_system.generate_response(user_input, use_rag=use_rag)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    main()
