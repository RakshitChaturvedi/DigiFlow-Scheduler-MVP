from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class JobLogStatus(str, Enum):
    COMPLETED = "completed"
    PAUSED = "paused"
    ABORTED_ISSUE = "aborted_issue"