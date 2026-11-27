"""Persistent learning submissions and authenticated attachment retrieval."""
from sqlalchemy import LargeBinary
from fastapi.responses import Response
from .main import app,Base,engine,dbdep,roles,Depends,HTTPException,Session,Mapped,mapped_column,String,JSON,uid,UploadFile,File,Assignment
from pydantic import BaseModel,Field
import datetime
staff=roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL")
student=roles("STUDENT")
class Work(Base):
    __tablename__="learning_work_submissions"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    school_id:Mapped[str]=mapped_column(String(36),index=True)
    owner_id:Mapped[str]=mapped_column(String(36),index=True)
    assignment_id:Mapped[str]=mapped_column(String(36))
    payload:Mapped[dict]=mapped_column(JSON)
class Evidence(Base):
    __tablename__="learning_work_evidence"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    work_id:Mapped[str]=mapped_column(String(36),index=True)
    name:Mapped[str]=mapped_column(String(255))
    data:Mapped[bytes]=mapped_column(LargeBinary)
Base.metadata.create_all(engine)
class WorkIn(BaseModel):
    assignment_id:str
    report:str=Field(min_length=1,max_length=30000)
@app.get("/api/v1/work/assignments")
def assignments(d:Session=Depends(dbdep),u=Depends(student)):
    return [{"id":a.id,"title":a.title,"description":a.description,"category":a.category} for a in d.query(Assignment).filter_by(school_id=u.school_id)]
@app.post("/api/v1/work")
def create(x:WorkIn,d:Session=Depends(dbdep),u=Depends(student)):
    a=d.query(Assignment).filter_by(id=x.assignment_id,school_id=u.school_id).first()
    if not a: raise HTTPException(404,"Assignment not found")
    w=Work(school_id=u.school_id,owner_id=u.id,assignment_id=a.id,payload={"title":a.title,"report":x.report,"status":"DRAFT","date":datetime.datetime.now(datetime.timezone.utc).isoformat()})
    d.add(w);d.commit();return {"id":w.id}
def owned(d,u,wid):
    q=d.query(Work).filter_by(id=wid,school_id=u.school_id)
    if u.role=="STUDENT": q=q.filter_by(owner_id=u.id)
    w=q.first()
    if not w: raise HTTPException(404,"Submission not found")
    return w
@app.post("/api/v1/work/{wid}/files")
async def upload(wid:str,file:UploadFile=File(...),d:Session=Depends(dbdep),u=Depends(student)):
    w=owned(d,u,wid)
    if w.payload["status"]!="DRAFT": raise HTTPException(409,"Submission locked")
    if d.query(Evidence).filter_by(work_id=wid).count()>=5: raise HTTPException(400,"Maximum five attachments")
    raw=await file.read(10*1024*1024+1)
    if len(raw)>10*1024*1024: raise HTTPException(413,"Maximum 10 MB per file")
    if not raw: raise HTTPException(400,"Empty file")
    name=(file.filename or "attachment").replace("\\","/").split("/")[-1][:200]
    if name.lower().rsplit(".",1)[-1] not in {"pdf","docx","txt","jpg","jpeg","png","mp4","webm"}: raise HTTPException(400,"Unsupported file extension")
    f=Evidence(work_id=wid,name=name,data=raw);d.add(f);d.commit();return {"id":f.id,"name":f.name}
@app.post("/api/v1/work/{wid}/submit")
def submit(wid:str,d:Session=Depends(dbdep),u=Depends(student)):
    w=owned(d,u,wid)
    if w.payload["status"]!="DRAFT": raise HTTPException(409,"Already submitted")
    w.payload={**w.payload,"status":"SUBMITTED"};d.commit();return {"status":"SUBMITTED"}
@app.get("/api/v1/work")
def list_work(d:Session=Depends(dbdep),u=Depends(roles("STUDENT","SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL"))):
    q=d.query(Work).filter_by(school_id=u.school_id)
    if u.role=="STUDENT": q=q.filter_by(owner_id=u.id)
    return [{"id":w.id,"owner_id":w.owner_id,**w.payload,"files":[{"id":f.id,"name":f.name} for f in d.query(Evidence).filter_by(work_id=w.id)]} for w in q if u.role=="STUDENT" or w.payload["status"]!="DRAFT"]
@app.get("/api/v1/work/{wid}/files/{fid}")
def download(wid:str,fid:str,d:Session=Depends(dbdep),u=Depends(roles("STUDENT","SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL"))):
    w=owned(d,u,wid)
    if u.role!="STUDENT" and w.payload["status"]=="DRAFT": raise HTTPException(404,"Not submitted")
    f=d.query(Evidence).filter_by(id=fid,work_id=wid).first()
    if not f: raise HTTPException(404,"File not found")
    return Response(f.data,media_type="application/octet-stream",headers={"Content-Disposition":"attachment","X-Content-Type-Options":"nosniff"})
class Review(BaseModel):
    score:float=Field(ge=0,le=100)
    feedback:str=Field(min_length=1,max_length=5000)
@app.post("/api/v1/work/{wid}/review")
def review(wid:str,x:Review,d:Session=Depends(dbdep),u=Depends(staff)):
    w=owned(d,u,wid)
    if w.payload["status"]!="SUBMITTED": raise HTTPException(409,"Not awaiting review")
    w.payload={**w.payload,**x.model_dump(),"status":"REVIEWED","reviewer":u.id};d.commit();return {"status":"REVIEWED"}
