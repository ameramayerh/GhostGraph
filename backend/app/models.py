from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import json

class Engagement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    scope: str
    authorized_by: str
    authorization_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "Active"
    
    # Progress Tracking
    total_findings: int = Field(default=0)
    filtered_findings: int = Field(default=0)
    
    # Relationships
    audit_logs: List["AuditLog"] = Relationship(back_populates="engagement")
    findings: List["Finding"] = Relationship(back_populates="engagement")

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    engagement_id: int = Field(foreign_key="engagement.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    user: str
    details: str
    
    engagement: Optional[Engagement] = Relationship(back_populates="audit_logs")

class Finding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    engagement_id: int = Field(foreign_key="engagement.id")
    title: str
    description: str
    
    # SAST specific fields
    file_path: str
    line_number: int
    code_snippet: str
    semgrep_rule_id: str
    
    severity: str = "Unknown"
    category: str
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI Enrichment Fields (Educational Security Pair Programmer)
    ai_explanation: Optional[str] = None       # The "WHAT", "WHY IT MATTERS"
    business_impact: Optional[str] = Field(default=None)
    remediation: Optional[str] = Field(default=None)
    code_patch: Optional[str] = Field(default=None)
    confidence_level: Optional[str] = Field(default=None)
    
    # AI Filtering Fields
    is_false_positive: bool = Field(default=False)
    filtering_status: str = Field(default="Pending") # Pending, Reviewed, Error
    
    engagement: Optional[Engagement] = Relationship(back_populates="findings")

class SystemSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    llm_provider: str = "local-llama3"
    api_key: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

