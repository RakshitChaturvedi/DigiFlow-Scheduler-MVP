from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

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

    def __repr__(self):
        return f"<Machine(id={self.id}, machine_id_code = '{self.machine_id_code}', type = '{self.machine_type}')>"

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
    current_status = Column(String, default="Pending", nullable=False)
    created_at = Column(DateTime, server_default=func.now()) # Timestamp when the record was created
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now()) # Timestamp of last update

    # RELATIONSHIPS
    # A production order can have many scheduled tasks associated with its various steps
    scheduled_tasks = relationship("ScheduledTask", back_populates="production_order")

    def __repr__(self):
        return(f"<ProductionOrder(id={self.id}, code='{self.order_id_code}', "
               f"qty={self.quantity_to_produce}, status='{self.current_status}')>")
    
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
    status = Column(String, default="Scheduled", nullable=False) #eg Scheduled, InProgress, Delayed etc

    # RELATIONSHIPS
    # to parent objects
    production_order = relationship("ProductionOrder", back_populates="scheduled_tasks")

    process_step_definition = relationship("ProcessStep", back_populates="scheduled_tasks_as_steps")
    assigned_machine = relationship("Machine", back_populates="scheduled_tasks")

    def __repr__(self):
        return(f"<ScheduledTask(id={self.id}, order_id={self.production_order_id}, "
               f"machine_id={self.assigned_machine_id}, start={self.start_time.strftime('%Y-%m-%d %H:%M')})>")
    