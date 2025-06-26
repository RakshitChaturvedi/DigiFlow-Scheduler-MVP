from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class ScheduledTaskStatus(str, Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class JobLogStatus(str, Enum):
    PENDING = "Pending" # A job log created but not yet scheduled/started
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"
    ABORTED = "Aborted"