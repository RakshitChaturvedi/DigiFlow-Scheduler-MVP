from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ScheduledTaskStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    BLOCKED = "blocked"

class JobLogStatus(str, Enum):
    PENDING = "pending" # A job log created but not yet scheduled/started
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

    def __str__(self):
        return self.value