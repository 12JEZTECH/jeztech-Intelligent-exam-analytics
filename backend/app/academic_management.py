from .main import app,Base,engine,dbdep,roles,Depends,HTTPException,Session,Mapped,mapped_column,String,JSON,uid,User,Learner,AcademicClass,BaseModel
from sqlalchemy import UniqueConstraint
import datetime
staff=roles("SCHOOL_ADMIN","DOS","PRINCIPAL")
class AcademicRecord(Base):
    __tablename__="academic_management_records"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    school_id:Mapped[str]=mapped_column(String(36),index=True)
    kind:Mapped[str]=mapped_column(String(30))
    key:Mapped[str]=mapped_column(String(100))
    payload:Mapped[dict]=mapped_column(JSON)
    __table_args__=(UniqueConstraint("school_id","kind","key"),)
Base.metadata.create_all(engine)
class Link(BaseModel):
    parent_id:str
    learner_id:str
class Allocation(BaseModel):
    learner_id:str
    class_id:str
class Term(BaseModel):
    name:str
    start:datetime.date
    end:datetime.date
def save(d,u,kind,key,payload):
    r=d.query(AcademicRecord).filter_by(school_id=u.school_id,kind=kind,key=key).first()
    if not r: r=AcademicRecord(school_id=u.school_id,kind=kind,key=key,payload=payload);d.add(r)
    else:r.payload=payload
    d.add(AcademicRecord(school_id=u.school_id,kind="audit",key=uid(),payload={"actor":u.id,"action":kind,"target":key,"date":datetime.datetime.now(datetime.timezone.utc).isoformat()}))
    d.commit();return {"saved":True}
@app.post("/api/v1/academic/parent-links")
def link(x:Link,d:Session=Depends(dbdep),u=Depends(staff)):
    if not d.query(User).filter_by(id=x.parent_id,school_id=u.school_id,role="PARENT").first() or not d.query(Learner).filter_by(id=x.learner_id,school_id=u.school_id).first():raise HTTPException(404,"Parent or learner not found")
    return save(d,u,"parent",x.parent_id+":"+x.learner_id,x.model_dump())
@app.post("/api/v1/academic/allocations")
def allocate(x:Allocation,d:Session=Depends(dbdep),u=Depends(staff)):
    if not d.query(Learner).filter_by(id=x.learner_id,school_id=u.school_id).first() or not d.query(AcademicClass).filter_by(id=x.class_id,school_id=u.school_id).first():raise HTTPException(404,"Learner or class not found")
    return save(d,u,"allocation",x.learner_id,x.model_dump())
@app.post("/api/v1/academic/terms")
def term(x:Term,d:Session=Depends(dbdep),u=Depends(staff)):
    if x.start>x.end or not x.name.strip() or len(x.name)>100:raise HTTPException(422,"Invalid term")
    return save(d,u,"term",x.name,x.model_dump(mode="json"))
@app.get("/api/v1/academic/register")
def register(d:Session=Depends(dbdep),u=Depends(staff)):
    return [{"kind":r.kind,**r.payload} for r in d.query(AcademicRecord).filter_by(school_id=u.school_id)]
@app.get("/api/v1/academic/parent")
def parent(d:Session=Depends(dbdep),u=Depends(roles("PARENT"))):
    out=[]
    for r in d.query(AcademicRecord).filter_by(school_id=u.school_id,kind="parent"):
        if r.payload["parent_id"]!=u.id:continue
        l=d.query(Learner).filter_by(id=r.payload["learner_id"],school_id=u.school_id).first()
        if l:out.append({"id":l.id,"name":l.first_name+" "+l.last_name,"admission":l.admission_number})
    return out
