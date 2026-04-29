import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    PATIENT = "patient"
    LAB_TECH = "lab_tech"
    PHARMACIST = "pharmacist"
    
    
