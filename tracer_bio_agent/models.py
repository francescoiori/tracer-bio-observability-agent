# models.py (SQLAlchemy models and Pydantic schemas)
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from tracer_bio_agent.database import Base


class Execution(Base):
    """Database model for storing execution details."""
    __tablename__ = "executions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)  # START or END
    timestamp = Column(DateTime, index=True)
    pid = Column(Integer, index=True)
    ppid = Column(Integer, index=True)
    uid = Column(Integer, index=True)
    command = Column(String, index=True)
    args = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    cpu_ticks = Column(Integer, nullable=True)

class Metrics(Base):
    """Database model for storing resource usage metrics."""
    __tablename__ = "metrics"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    pid = Column(Integer, ForeignKey("executions.pid"), index=True)
    ppid = Column(Integer, index=True, nullable=True)
    cpu = Column(Float)
    mem = Column(Float)
    vsz = Column(Integer)
    rss = Column(Integer)
    tty = Column(String, nullable=True)
    stat = Column(String)
    start = Column(String)
    time = Column(String)
    command = Column(String)
    snapshot_time = Column(DateTime)

class ProcessedExecution(Base):
    """Database model for storing processed execution events."""
    __tablename__ = "processed_executions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    event_type = Column(String, index=True)  # START or END
    timestamp = Column(DateTime, index=True)
    pid = Column(Integer, index=True)
    ppid = Column(Integer, index=True)
    uid = Column(Integer, index=True)
    command = Column(String, index=True)
    args = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    cpu_ticks = Column(Integer, nullable=True)
    pipeline = Column(String, index=True)
    run_id = Column(String, index=True)


class ProcessedMetrics(Base):
    """Database model for storing filtered and processed metrics."""
    __tablename__ = "processed_metrics"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    pid = Column(Integer, index=True)
    cpu = Column(Float)
    mem = Column(Float)
    vsz = Column(Integer)
    rss = Column(Integer)
    tty = Column(String, nullable=True)
    stat = Column(String)
    start = Column(String)
    time = Column(String)
    command = Column(String, index=True)
    snapshot_time = Column(DateTime)
    pipeline = Column(String, index=True)  # The pipeline it belongs to


class ExecutionLogSchema(BaseModel):
    event_type: str
    timestamp: datetime
    pid: int
    ppid: int
    uid: int
    command: str
    args: Optional[str] = None
    duration: Optional[int] = None
    cpu_ticks: Optional[int] = None


class MetricsSchema(BaseModel):
    user: str
    pid: int
    ppid: Optional[int]
    cpu: float
    mem: float
    vsz: int
    rss: int
    tty: Optional[str]
    stat: str
    start: str
    time: str
    command: str
    snapshot_time: datetime

class ProcessedExecutionSchema(BaseModel):
    """Pydantic schema for processed execution events."""
    user: str
    event_type: str  # START or END
    timestamp: datetime
    pid: int
    ppid: int
    uid: int
    command: str
    args: Optional[str] = None
    duration: Optional[int] = None
    cpu_ticks: Optional[int] = None
    pipeline: str
    run_id: str


class ProcessedMetricsSchema(BaseModel):
    """Pydantic schema for processed metrics logs."""
    user: str
    pid: int
    cpu: float
    mem: float
    vsz: int
    rss: int
    tty: Optional[str]
    stat: str
    start: str
    time: str
    command: str
    snapshot_time: datetime
    pipeline: str