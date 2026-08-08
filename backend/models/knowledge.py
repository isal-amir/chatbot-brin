from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from core.database import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
