"""Account-owned timed learning assignments, separate from legacy attempts."""
import datetime, math
from pydantic import BaseModel,Field
from sqlalchemy import UniqueConstraint
from .main import app,Base,engine,dbdep,roles,Depends,HTTPException,Session,Mapped,mapped_column,String,JSON,uid,User
from .exam_studio import GeneratedPaper
staff=roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL")
student=roles("STUDENT")
def now(): return datetime.datetime.now(datetime.timezone.utc)
class LearningTask(Base):
    __tablename__="learning_portal_tasks"
    __table_args__=(UniqueConstraint("school_id","student_id","paper_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    school_id:Mapped[str]=mapped_column(String(36),index=True)
    student_id:Mapped[str]=mapped_column(String(36),index=True)
    paper_id:Mapped[str]=mapped_column(String(36))
    payload:Mapped[dict]=mapped_column(JSON)
Base.metadata.create_all(engine)
class Assign(BaseModel):
    student_id:str
    paper_id:str
    minutes:int=Field(30,ge=1,le=240)
@app.post("/api/v1/learning/tasks")
def assign(x:Assign,d:Session=Depends(dbdep),u=Depends(staff)):
    s=d.query(User).filter_by(id=x.student_id,school_id=u.school_id,role="STUDENT").first()
    p=d.query(GeneratedPaper).filter_by(id=x.paper_id,school_id=u.school_id).first()
    if not s or not p: raise HTTPException(404,"Student account or paper not found")
    if d.query(LearningTask).filter_by(school_id=u.school_id,student_id=s.id,paper_id=p.id).first(): raise HTTPException(409,"Already assigned")
    t=LearningTask(school_id=u.school_id,student_id=s.id,paper_id=p.id,payload={"title":p.payload["subject"]+" — "+p.payload["topic"],"questions":p.payload["questions"],"minutes":x.minutes,"status":"ASSIGNED","answers":{}})
    d.add(t);d.commit();return {"id":t.id}
def public(t):
    p=t.payload
    return {"id":t.id,"title":p["title"],"minutes":p["minutes"],"status":p["status"],"deadline":p.get("deadline"),"answers":p.get("answers",{}),"score":p.get("score"),"maximum":p.get("maximum"),"questions":[{k:q[k] for k in ("id","prompt","options","marks")} for q in p["questions"]] if p["status"]=="STARTED" else []}
@app.get("/api/v1/learning/tasks")
def tasks(d:Session=Depends(dbdep),u=Depends(student)):
    return [public(t) for t in d.query(LearningTask).filter_by(school_id=u.school_id,student_id=u.id)]
def own(d,u,tid):
    t=d.query(LearningTask).filter_by(id=tid,school_id=u.school_id,student_id=u.id).with_for_update().first()
    if not t: raise HTTPException(404,"Task not found")
    return t
@app.post("/api/v1/learning/tasks/{tid}/start")
def start(tid:str,d:Session=Depends(dbdep),u=Depends(student)):
    t=own(d,u,tid)
    if t.payload["status"]=="ASSIGNED":
        t.payload={**t.payload,"status":"STARTED","deadline":(now()+datetime.timedelta(minutes=t.payload["minutes"])).isoformat()};d.commit()
    return public(t)
class Answers(BaseModel):
    answers:dict[str,str]
@app.put("/api/v1/learning/tasks/{tid}/answers")
def save(tid:str,x:Answers,d:Session=Depends(dbdep),u=Depends(student)):
    t=own(d,u,tid);p=t.payload
    if p["status"]!="STARTED" or now()>=datetime.datetime.fromisoformat(p["deadline"]): raise HTTPException(409,"Assessment closed")
    allowed={q["id"]:q["options"] for q in p["questions"]}
    if any(k not in allowed or v not in allowed[k] for k,v in x.answers.items()): raise HTTPException(422,"Invalid answer")
    t.payload={**p,"answers":x.answers};d.commit();return {"saved":True}
@app.post("/api/v1/learning/tasks/{tid}/submit")
def submit(tid:str,d:Session=Depends(dbdep),u=Depends(student)):
    t=own(d,u,tid);p=t.payload
    if p["status"]!="STARTED": raise HTTPException(409,"Not active")
    score=sum(q["marks"] for q in p["questions"] if p["answers"].get(q["id"])==q["answer"])
    t.payload={**p,"status":"MARKED","score":score,"maximum":sum(q["marks"] for q in p["questions"])};d.commit();return public(t)
@app.get("/api/v1/learning/results")
def results(d:Session=Depends(dbdep),u=Depends(staff)):
    return [{"student_id":t.student_id,**public(t)} for t in d.query(LearningTask).filter_by(school_id=u.school_id) if t.payload["status"]=="MARKED"]
