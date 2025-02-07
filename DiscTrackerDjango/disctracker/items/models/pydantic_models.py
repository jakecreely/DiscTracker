from typing import List
from pydantic import BaseModel, Field

class CexIdValidator(BaseModel):
    cex_id: str = Field(pattern=r'^[A-Za-z0-9]+$')

class ItemDetail(BaseModel):
    boxId: str
    boxName: str
    sellPrice: float 
    exchangePrice: float
    cashPrice: float
        
class BoxDetailsWrapper(BaseModel):
    boxDetails: List[ItemDetail]

class CexApiError(BaseModel):
    code: str
    internal_message: str
    moreInfo: List[str]
class CexItemApiResponseData(BaseModel):
    ack: str # Acknolwegment/Status
    data: BoxDetailsWrapper
    error: CexApiError
    
class CexItemApiResponseWrapper(BaseModel):
    response: CexItemApiResponseData

# CEX API Response Structure
# "response": {
#   "ack": "Success",
#   "data": {
    #   "boxDetails": [ItemDetail]
    # },
#   "error": {
#       "code": "",
#       "internal_message": "",
#       "moreInfo": []
#   }
# }