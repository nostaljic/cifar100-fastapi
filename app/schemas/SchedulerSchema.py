from pydantic import BaseModel
from typing import Any


class SchedulerCommonResponseSchema(BaseModel):
    status: Any
