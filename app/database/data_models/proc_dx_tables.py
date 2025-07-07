from sqlalchemy import Column, String, BigInteger, Text
from database.session import Base

"""
Procedure and Diagnosis Codes Database Models Module

This module defines the SQLAlchemy models for procedure and diagnosis codes.
It includes models for:
1. ProcedureCodes: Healthcare procedure codes with their metadata
2. DiagnosisCodes: Diagnosis codes with their associated conditions and descriptions
"""


class ProcedureCodes(Base):
    """SQLAlchemy model for storing procedure codes and their metadata.

    This model stores procedure codes along with their categories, descriptions,
    and aggregated visit counts.
    """

    __tablename__ = "proc_codes"

    procedure_code = Column(
        Text,
        primary_key=True,
        name="Procedure Code",
        doc="Unique procedure code identifier",
    )
    category = Column(
        Text,
        name="Procedure Code Category",
        nullable=True,
        doc="Category of the procedure code",
    )
    description = Column(
        Text,
        name="Procedure Code Description",
        nullable=True,
        doc="Description of the procedure code",
    )
    sub_category = Column(
        Text,
        name="Procedure Code Sub Category",
        nullable=True,
        doc="Sub-category of the procedure code",
    )
    sub_type = Column(
        Text,
        name="Procedure Sub Type",
        nullable=True,
        doc="Sub-type classification of the procedure",
    )
    proc_type = Column(
        Text,
        name="Procedure Type",
        nullable=True,
        doc="Type classification of the procedure",
    )
    visits = Column(
        BigInteger,
        name="Visits",
        nullable=True,
        doc="Number of visits associated with this procedure code",
    )


class DiagnosisCodes(Base):
    """SQLAlchemy model for storing diagnosis codes and their metadata.

    This model stores diagnosis codes along with their conditions, descriptions,
    and hierarchical classification (chapter and section).
    """

    __tablename__ = "dx_codes"

    diagnosis_code = Column(
        Text,
        primary_key=True,
        name="Visit Primary Diagnosis Code",
        doc="Unique diagnosis code identifier",
    )
    condition = Column(
        Text,
        name="Visit Primary Diagnosis Code Condition",
        nullable=True,
        doc="Condition associated with the diagnosis code",
    )
    cancer_description = Column(
        Text,
        name="Cancer Condition Description",
        nullable=True,
        doc="Description of cancer condition if applicable",
    )
    chapter = Column(
        Text,
        name="Visit Primary Diagnosis Code Chapter",
        nullable=True,
        doc="Chapter classification of the diagnosis code",
    )
    description = Column(
        Text,
        name="Visit Primary Diagnosis Code Description",
        nullable=True,
        doc="Description of the diagnosis code",
    )
    section = Column(
        Text,
        name="Visit Primary Diagnosis Code Section",
        nullable=True,
        doc="Section classification of the diagnosis code",
    )
