from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DocumentStatusHistory(Base):
    __tablename__ = "document_status_history"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    old_status = Column(String)
    new_status = Column(String)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="status_history")
