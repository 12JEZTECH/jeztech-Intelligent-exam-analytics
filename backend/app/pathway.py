from .main import app,roles,Depends,HTTPException
from pydantic import BaseModel,Field
class PathwayInput(BaseModel):
    academic:float=Field(ge=0,le=100)
    practical:float=Field(ge=0,le=100)
    grade7:float=Field(ge=0,le=100)
    grade9:float=Field(ge=0,le=100)
    interest:float=Field(ge=0,le=100)
@app.post("/api/v1/analytics-tools/pathway")
def pathway(x:PathwayInput,u=Depends(roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL"))):
    growth=max(0,min(100,50+2.5*(x.grade9-x.grade7)))
    return {"index":round(.55*x.academic+.20*x.practical+.15*growth+.10*x.interest,2),"growth":growth,"advisory":True,"note":"School advisory model, not an official placement decision"}
