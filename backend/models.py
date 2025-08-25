from typing import List, Optional, Any
from pydantic import BaseModel

class SearchQuery(BaseModel):
    origins: List[str]
    destinations: List[str]
    depart_date: str
    return_date: Optional[str] = None
    adults: int = 1
    days_flex: int = 2
    limit_per_route: int = 40
