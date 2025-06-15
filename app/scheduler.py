import collections
import logging
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import pandas as pd
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Machine, ProcessStep, ProductionOrder, ScheduledTask

