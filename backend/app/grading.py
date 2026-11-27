from .main import app,Base,engine,dbdep,roles,Depends,HTTPException,Session,Mapped,mapped_column,String,JSON,BaseModel,Field
staff=roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL")
class GradePolicy(Base):
    __tablename__="school_grade_policies"
    school_id:Mapped[str]=mapped_column(String(36),primary_key=True)
    curriculum:Mapped[str]=mapped_column(String(10),primary_key=True)
    boundaries:Mapped[list]=mapped_column(JSON)
Base.metadata.create_all(engine)
class Boundary(BaseModel):
    label:str
    minimum:float=Field(ge=0,le=100)
    points:int=Field(ge=1,le=12)
class Policy(BaseModel):
    boundaries:list[Boundary]
@app.put("/api/v1/grading/{curriculum}")
def set_policy(curriculum:str,x:Policy,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","DOS"))):
    labels=["EE1","EE2","ME1","ME2","AE1","AE2","BE1","BE2"] if curriculum=="CBC" else ["A","A-","B+","B","B-","C+","C","C-","D+","D","D-","E"] if curriculum=="844" else []
    b=x.boundaries
    if not labels or [v.label for v in b]!=labels or b[-1].minimum!=0 or any(b[i].minimum<=b[i+1].minimum for i in range(len(b)-1)) or [v.points for v in b]!=list(range(len(labels),0,-1)): raise HTTPException(422,"Provide all grade labels in descending order, strictly decreasing boundaries ending at zero and descending points")
    p=d.get(GradePolicy,(u.school_id,curriculum))
    if not p: p=GradePolicy(school_id=u.school_id,curriculum=curriculum,boundaries=[]);d.add(p)
    p.boundaries=[v.model_dump() for v in b];d.commit();return {"saved":True}
@app.get("/api/v1/grading/{curriculum}")
def policy(curriculum:str,d:Session=Depends(dbdep),u=Depends(staff)):
    p=d.get(GradePolicy,(u.school_id,curriculum));return {"boundaries":p.boundaries if p else []}
class Score(BaseModel):
    percentage:float=Field(ge=0,le=100)
@app.post("/api/v1/grading/{curriculum}/calculate")
def calculate(curriculum:str,x:Score,d:Session=Depends(dbdep),u=Depends(staff)):
    p=d.get(GradePolicy,(u.school_id,curriculum))
    if not p: raise HTTPException(409,"Configure approved school grading boundaries first")
    return next(v for v in p.boundaries if x.percentage>=v["minimum"])
