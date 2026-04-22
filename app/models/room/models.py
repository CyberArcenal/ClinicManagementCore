from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Room(BaseModel):
    __tablename__ = "rooms"
    
    room_number = Column(String, unique=True, nullable=False)
    room_type = Column(String)  # consultation, treatment, exam, ward
    capacity = Column(Integer, default=1)
    is_available = Column(Boolean, default=True)
    notes = Column(Text)
    
    appointments = relationship("Appointment", back_populates="room")  # if room assigned

# Add room_id to Appointment model