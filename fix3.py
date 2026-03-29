--- src/blockbt/api/routes/results.py
+++ src/blockbt/api/routes/results.py
@@ -1,6 +1,7 @@
 from typing import Any

 import pandas as pd
+from pydantic import BaseModel
 from fastapi import APIRouter, Depends, HTTPException

 from blockbt.api.dependencies import get_api_key
@@ -12,8 +13,6 @@

 router = APIRouter(dependencies=[Depends(get_api_key)])

-from pydantic import BaseModel
 class AIAnalysisResponse(BaseModel):
     prompt: str | None
     report: str
