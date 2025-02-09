from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

class CexIdValidator(BaseModel):
    cex_id: str = Field(pattern=r'^[A-Za-z0-9]+$')

class CexApiItemDetail(BaseModel):
    boxId: str = Field(..., pattern=r'^[A-Za-z0-9]+$')    
    boxName: str
    sellPrice: Decimal 
    exchangePrice: Decimal
    cashPrice: Decimal
    
class CexApiItemDetailCreateUpdate(BaseModel):
    boxId: str
    boxName: Optional[str] = None
    sellPrice: Optional[Decimal] = None 
    exchangePrice: Optional[Decimal] = None
    cashPrice: Optional[Decimal] = None

class ItemDetailUpdate(BaseModel):
    cex_id: str
    title: Optional[str] = None
    sell_price: Optional[Decimal] = None
    exchange_price: Optional[Decimal] = None
    cash_price: Optional[Decimal] = None
        
class BoxDetailsWrapper(BaseModel):
    boxDetails: List[CexApiItemDetail]

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