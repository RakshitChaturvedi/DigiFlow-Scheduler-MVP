from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, event, Table
from sqlalchemy.orm import declarative_base, relationship, Session, attributes, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.exc import NoResultFound
from sqlalchemy import event, inspect
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from datetime import datetime

import uuid

from backend.app.enums import OrderStatus, JobLogStatus, ScheduledTaskStatus


import datetime

Base = declarative_base()

# --- User-Machine Association Table ---
user_machine_association = Table(
    'user_machine_association',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('machine_id', Integer, ForeignKey('machines.id', ondelete='CASCADE'), primary_key=True)
)

# --- MACHINE MODEL ---
class Machine(Base):
    # A physical machine or workstation in the manufacturing facility.

    __tablename__ = 'machines'

    id = Column(Integer, primary_key=True, index=True) # Primary key for the machine
    machine_id_code = Column(String, unique=True, index=True, nullable=False) # "VMC-001", "HMC-A"
    machine_type = Column(String, nullable=False) # "VMC", "HMC", "Grinder"

    # setup_time_mins here would be a default or average setup time for the machine type
    # For sequence-dependant setup, this would be more complex, like a seperate table
    default_setup_time_mins = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # RELATIONSHIPS
    # A machine can have many scheduled tasks assigned to it
    scheduled_tasks = relationship("ScheduledTask", back_populates="assigned_machine")
    # A machine can have many downtime events
    downtime_events = relationship("DowntimeEvent", back_populates="machine", cascade="all, delete", passive_deletes=True)

    authorized_operators = relationship(
        "User",
        secondary=user_machine_association,
        back_populates="authorized_machines"
    )

    def __repr__(self):
        return f"<Machine(id={self.id}, machine_id_code = '{self.machine_id_code}', type = '{self.machine_type}')>"

# --- PROCESS STEP MODEL ---
class ProcessStep(Base):
    # Represents a generic step in production process route, defines WHAT needs to be done and
    # WHICH TYPE of machine can do it, does NOT link to a specific physical machine

    __tablename__ = 'process_steps'

    id = Column(Integer, primary_key=True, index=True)

    # generic identifier for a product's entire process route, eg "dabur_cap_route"
    product_route_id = Column(String, index=True, nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String, nullable=False)
    required_machine_type = Column(String, nullable=False)
    base_duration_per_unit_mins = Column(Integer, nullable=False)

    # RELATIONSHIPS
    # A process_step will be referenced by many scheduled_tasks. We define it here to easy lookup from scheduled_task back to its definition
    scheduled_tasks_as_steps = relationship("ScheduledTask", back_populates="process_step_definition")

    def __repr__(self):
        return (f"<ProcessStep(id={self.id}, route='{self.product_route_id}', "
                f"step_number={self.step_number}, required_machine_type = '{self.required_machine_type}')>")
    
# --- PRODUCTION ORDER MODEL ---
class ProductionOrder(Base):
    # Represents a customer order for a specific product, quantity, due date and priority.
    # Core demand that drives scheduling

    __tablename__ = 'production_orders'

    id = Column(Integer, primary_key=True, index=True)
    order_id_code = Column(String, unique=True, index=True, nullable=False) # Eg: ORD-250614-02
    product_name = Column(String, nullable=True)
    product_route_id = Column(String, nullable=False)
    quantity_to_produce = Column(Integer, nullable=False)
    priority = Column(Integer, default=0, nullable=False) # Higher the number, Higher priority
    arrival_time = Column(DateTime, nullable=False, default=func.now())
    due_date = Column(DateTime, nullable=True) # Optional Hard Deadline
    current_status: Mapped[OrderStatus] = mapped_column(SqlEnum(OrderStatus, name="order_status_enum", native_enum=False), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default=func.now()) # Timestamp when the record was created
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now()) # Timestamp of last update

    logs = relationship("JobLog", back_populates="production_order")

    # RELATIONSHIPS
    # A production order can have many scheduled tasks associated with its various steps
    scheduled_tasks = relationship("ScheduledTask", back_populates="production_order")

    def __repr__(self):
        return(f"<ProductionOrder(id={self.id}, code='{self.order_id_code}', "
               f"qty={self.quantity_to_produce}, status='{self.current_status}')>")

# --- SCHEDULED TASK MODEL ---    
class ScheduledTask(Base):
    # Represents a specific instance of a process step being scheduled on a particular machine for a given
    # production order. this is the output of your scheduling algorithm
    
    __tablename__ = 'scheduled_tasks'

    id=Column(Integer, primary_key=True, index=True)
    production_order_id = Column(Integer, ForeignKey('production_orders.id'), nullable=False)
    process_step_id = Column(Integer, ForeignKey('process_steps.id'), nullable=False)
    assigned_machine_id = Column(Integer, ForeignKey('machines.id'), nullable=False)

    # Scheduled start and end times for this specific task instance
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Additional Fields to store derived info from scheduling or actual execution
    scheduled_duration_mins = Column(Integer, nullable=False)
    status: Mapped[ScheduledTaskStatus] = mapped_column(SqlEnum(ScheduledTaskStatus, name="scheduled_task_status_enum", native_enum=False), default=ScheduledTaskStatus.SCHEDULED, nullable=False)
    archived = mapped_column(Boolean, default=False)
    job_id_code = Column(String, unique=True, nullable=True) 
    scheduled_time = Column(DateTime, nullable=True)
    block_reason = Column(String, nullable=True)

    # RELATIONSHIPS
    # to parent objects
    production_order = relationship("ProductionOrder", back_populates="scheduled_tasks")
    process_step_definition = relationship("ProcessStep", back_populates="scheduled_tasks_as_steps")
    assigned_machine = relationship("Machine", back_populates="scheduled_tasks")

    def __repr__(self):
        return(f"<ScheduledTask(id={self.id}, order_id={self.production_order_id}, "
               f"machine_id={self.assigned_machine_id}, start={self.start_time.strftime('%Y-%m-%d %H:%M')})>")

# --- DOWNTIME EVENT MODEL ---
class DowntimeEvent(Base):
    __tablename__ = 'downtime_events'

    id = Column(Integer, primary_key=True, index=True)

    machine_id = Column(Integer, ForeignKey('machines.id', ondelete='CASCADE'), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reason = Column(String, nullable=False)
    comments = Column(Text, nullable=True)

    #Relationship to machine
    machine = relationship("Machine", back_populates="downtime_events")

    def __repr__(self):
        return(f"<DowntimeEvent(id={self.id}, machine_id={self.machine_id}, "
               f"start = '{self.start_time.strftime('%Y-%m-%d %H:%M')}, reason = '{self.reason}'>")

# --- JOB LOG MODEL ---    
class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys to link this log to everything it describes
    production_order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    process_step_id = Column(Integer, ForeignKey("process_steps.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    # The most important columns: The actual times
    actual_start_time = Column(DateTime(timezone=True), nullable=False)
    actual_end_time = Column(DateTime(timezone=True), nullable=True) # Nullable because it's not set until the job is done

    # Additional useful information
    status: Mapped[JobLogStatus] = mapped_column(SqlEnum(JobLogStatus, name="joblog_status_enum", native_enum=False), default=JobLogStatus.COMPLETED) # e.g., 'completed', 'paused', 'aborted_issue'
    remarks = Column(Text, nullable=True) # Any notes from the operator

    # Relationships to access the full objects from a log entry
    production_order = relationship("ProductionOrder", back_populates="logs")
    process_step = relationship("ProcessStep")
    machine = relationship("Machine")

# --- USER MODEL ---
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    authorized_machines = relationship(
        "Machine",
        secondary=user_machine_association,
        back_populates="authorized_operators"
    )

# --- Consolidated SQLAlchemy Event Listener for All Validations (3.1.1 and 3.1.2) ---
@event.listens_for(Session, "before_flush")
def validate_before_flush(session, flush_context, instances):
    for obj in session.new.union(session.dirty):
        
        # --- 3.1.1. Unique Constraint Validation ---
        # Using attributes.get_history().has_changes() for universal compatibility
        
        if isinstance(obj, ProductionOrder):
            hist_order_id = attributes.get_history(obj, 'order_id_code')
            if obj in session.new or hist_order_id.has_changes():
                existing = session.query(ProductionOrder).filter(
                    ProductionOrder.order_id_code == obj.order_id_code,
                    ProductionOrder.id != obj.id
                ).first()
                if existing:
                    raise ValueError(f"Duplicate ProductionOrder.order_id_code: '{obj.order_id_code}' already exists.")
        
        elif isinstance(obj, Machine):
            hist_machine_id = attributes.get_history(obj, 'machine_id_code')
            if obj in session.new or hist_machine_id.has_changes():
                existing = session.query(Machine).filter(
                    Machine.machine_id_code == obj.machine_id_code,
                    Machine.id != obj.id
                ).first()
                if existing:
                    raise ValueError(f"Duplicate Machine.machine_id_code: '{obj.machine_id_code}' already exists in another record.")
        
        elif isinstance(obj, ProcessStep):
            hist_route_id = attributes.get_history(obj, 'product_route_id')
            hist_step_num = attributes.get_history(obj, 'step_number')
            if obj in session.new or hist_route_id.has_changes() or hist_step_num.has_changes():
                existing = session.query(ProcessStep).filter(
                    ProcessStep.product_route_id == obj.product_route_id,
                    ProcessStep.step_number == obj.step_number,
                    ProcessStep.id != obj.id
                ).first()
                if existing:
                    raise ValueError(f"Duplicate ProcessStep: A step with route '{obj.product_route_id}' and step number '{obj.step_number}' already exists.")

        # --- 3.1.2. Business Logic Validation (Numerical & Date/Time Ranges) ---
        
        if isinstance(obj, ProductionOrder):
            if obj.quantity_to_produce is not None and obj.quantity_to_produce <= 0:
                raise ValueError(f"ProductionOrder quantity_to_produce must be positive, got {obj.quantity_to_produce}.")
            if obj.due_date and obj.arrival_time and obj.due_date < obj.arrival_time:
                raise ValueError(f"ProductionOrder due_date ({obj.due_date}) cannot be before arrival_time ({obj.arrival_time}).")
        
        elif isinstance(obj, ProcessStep):
            if obj.step_number is not None and obj.step_number <= 0:
                raise ValueError(f"ProcessStep step_number must be positive, got {obj.step_number}.")
            if obj.base_duration_per_unit_mins is not None and obj.base_duration_per_unit_mins <= 0:
                raise ValueError(f"ProcessStep base_duration_per_unit_mins must be positive, got {obj.base_duration_per_unit_mins}.")
            
        elif isinstance(obj, Machine):
            if obj.default_setup_time_mins is not None and obj.default_setup_time_mins < 0:
                raise ValueError(f"Machine default_setup_time_mins cannot be negative, got {obj.default_setup_time_mins}.")

        elif isinstance(obj, ScheduledTask):
            if obj.start_time and obj.end_time and obj.end_time <= obj.start_time:
                raise ValueError(f"ScheduledTask end_time ({obj.end_time}) must be after start_time ({obj.start_time}).")
            if obj.scheduled_duration_mins is not None and obj.scheduled_duration_mins <= 0:
                raise ValueError(f"ScheduledTask scheduled_duration_mins must be positive, got {obj.scheduled_duration_mins}.")

        elif isinstance(obj, DowntimeEvent):
            if obj.start_time and obj.end_time and obj.end_time <= obj.start_time:
                raise ValueError(f"DowntimeEvent end_time ({obj.end_time}) must be after start_time ({obj.start_time}).")
            if not obj.reason or not obj.reason.strip():
                raise ValueError("DowntimeEvent.reason cannot be empty.")

        elif isinstance(obj, JobLog):
            if obj.actual_start_time and obj.actual_end_time and obj.actual_end_time <= obj.actual_start_time:
                raise ValueError(f"JobLog actual_end_time ({obj.actual_end_time}) must be after actual_start_time ({obj.actual_start_time}).")
            # The .status check here will be removed/refined in 3.1.3 once Enums are fully leveraged.
            # For now, if you're getting an Enum, this might not be needed or would raise if it's an invalid string.
            # If obj.status is an Enum member, obj.status.value might be needed for string comparison.
            # This validation will be handled more robustly by the Enum itself and Pydantic.

        # --- Foreign Key Existence Validation ---
        
        if isinstance(obj, JobLog):
            if obj.production_order_id:
                try:
                    session.query(ProductionOrder.id).filter_by(id=obj.production_order_id).one()
                except NoResultFound:
                    raise ValueError(f"JobLog refers to missing ProductionOrder ID '{obj.production_order_id}'.")
            
            if obj.process_step_id:
                try:
                    session.query(ProcessStep.id).filter_by(id=obj.process_step_id).one()
                except NoResultFound:
                    raise ValueError(f"JobLog refers to missing ProcessStep ID '{obj.process_step_id}'.")
            
            if obj.machine_id:
                try:
                    session.query(Machine.id).filter_by(id=obj.machine_id).one()
                except NoResultFound:
                    raise ValueError(f"JobLog refers to missing Machine ID '{obj.machine_id}'.")
        
        elif isinstance(obj, ScheduledTask):
            if obj.production_order_id:
                try:
                    session.query(ProductionOrder.id).filter_by(id=obj.production_order_id).one()
                except NoResultFound:
                    raise ValueError(f"ScheduledTask refers to missing ProductionOrder ID '{obj.production_order_id}'.")
            
            if obj.process_step_id:
                try:
                    session.query(ProcessStep.id).filter_by(id=obj.process_step_id).one()
                except NoResultFound:
                    raise ValueError(f"ScheduledTask refers to missing ProcessStep ID '{obj.process_step_id}'.")
            
            if obj.assigned_machine_id:
                try:
                    session.query(Machine.id).filter_by(id=obj.assigned_machine_id).one()
                except NoResultFound:
                    raise ValueError(f"ScheduledTask refers to missing Machine ID '{obj.assigned_machine_id}'.")

        elif isinstance(obj, DowntimeEvent):
            if obj.machine_id:
                try:
                    session.query(Machine.id).filter_by(id=obj.machine_id).one()
                except NoResultFound:
                    raise ValueError(f"DowntimeEvent refers to missing Machine ID '{obj.machine_id}'.")

