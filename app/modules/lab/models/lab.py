from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from app.common.models.base import BaseModel
from app.modules.lab.enums.base import LabStatus


class LabResult(BaseModel):
    __tablename__ = "lab_results"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    ehr_id = Column(Integer, ForeignKey("ehr.id"))
    test_name = Column(String, nullable=False)
    requested_by_id = Column(Integer, ForeignKey("doctor_profiles.id"))
    performed_by_id = Column(Integer, ForeignKey("lab_tech_profiles.id"))
    requested_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime)
    status = Column(Enum(LabStatus), default=LabStatus.PENDING)
    result_data = Column(Text)  # JSON or structured text
    normal_range = Column(String)
    remarks = Column(Text)

    # Relationships with full module paths
    patient = relationship(
        "app.modules.patients.models.models.Patient", back_populates="lab_results"
    )
    ehr_visit = relationship(
        "app.modules.ehr.models.base.EHR", back_populates="lab_requests"
    )
    requested_by = relationship(
        "app.modules.staff.models.doctor_profile.DoctorProfile",
        foreign_keys=[requested_by_id],
    )
    performed_by = relationship(
        "app.modules.staff.models.labtech_profile.LabTechProfile",
        back_populates="lab_results",
    )
