from pydantic import BaseModel, ConfigDict
from fastapi import WebSocket
from typing import List, Any

class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str
    name: str
    ws: WebSocket
    online: bool = True
    powers: List[int] = []
    code: Any = None