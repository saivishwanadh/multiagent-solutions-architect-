import os
import json
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.config.settings import get_llm

class OrgLessonsMemory:
    """
    Singleton-style Vector DB for Organizational Lessons.
    Uses ChromaDB and GoogleGenerativeAIEmbeddings for retrieval.
    """
    _instance = None
    
    def __init__(self):
        self.persist_directory = os.path.join(os.path.dirname(__file__), "..", "..", ".chroma_db")
        self.vector_store = self._initialize_vector_store()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def _initialize_vector_store(self) -> Chroma:
        """Initializes Chroma DB pointing to the persist directory."""
        vector_store = Chroma(
            collection_name="org_lessons",
            persist_directory=self.persist_directory
        )
        return vector_store
        
    def get_relevant_lessons(self, query: str, k: int = 3) -> list[str]:
        """Searches the vector DB and returns formatted lesson strings."""
        if not self.vector_store:
            return []
            
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"Error querying Vector DB: {e}")
            return []

    def add_lesson(self, category: str, context: str, lesson: str, directive: str) -> bool:
        """Dynamically injects a new organizational lesson into ChromaDB."""
        if not self.vector_store:
            return False
            
        import uuid
        lesson_id = str(uuid.uuid4())
        
        content = (
            f"Category: {category}\n"
            f"Context: {context}\n"
            f"Lesson: {lesson}\n"
            f"Directive: {directive}"
        )
        
        doc = Document(
            page_content=content, 
            metadata={"id": lesson_id, "category": category}
        )
        
        try:
            self.vector_store.add_documents([doc])
            print(f"\n[Memory DB] Successfully injected new organizational memory into ChromaDB: {category}")
            return True
        except Exception as e:
            print(f"Error injecting into Vector DB: {e}")
            return False

# Helper function to easily retrieve lessons in graphs
def get_lessons(query: str, k: int = 3) -> list[str]:
    memory = OrgLessonsMemory.get_instance()
    return memory.get_relevant_lessons(query, k)
