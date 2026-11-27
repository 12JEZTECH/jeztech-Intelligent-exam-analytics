"""Additive school-scoped assessment records; existing tables untouched."""
from pydantic import BaseModel, Field
from sqlalchemy import UniqueConstraint
from .main import app, Base, engine, dbdep, roles, Exam, Learner, uid, Session, Depends, HTTPException, Mapped, mapped_column, String, Float, ForeignKey
class SubjectMark(Base):
    __tablename__="analytics_subject_marks"
    __table_args__=(UniqueConstraint("school_id","exam_id","learner_id","subject"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    school_id:Mapped[str]=mapped_column(String(36),index=True)
    exam_id:Mapped[str]=mapped_column(String(36),index=True)
    learner_id:Mapped[str]=mapped_column(String(36))
    subject:Mapped[str]=mapped_column(String(120))
    score:Mapped[float|None]=mapped_column(Float,nullable=True)
    maximum:Mapped[float]=mapped_column(Float)
    status:Mapped[str]=mapped_column(String(20))
Base.metadata.create_all(engine)
staff=roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL")
class MarkIn(BaseModel):
    learner_id:str
    subject:str=Field(min_length=1,max_length=120)
    score:float|None=None
    maximum:float=Field(gt=0,le=10000)
    status:str="ASSESSED"
def exam_for(d,u,eid):
    e=d.query(Exam).filter_by(id=eid,school_id=u.school_id).first()
    if not e: raise HTTPException(404,"Exam not found")
    return e
@app.post("/api/v1/analytics/{eid}/marks")
def save_marks(eid:str, rows:list[MarkIn], d:Session=Depends(dbdep),u=Depends(staff)):
    e=exam_for(d,u,eid)
    if e.status!="DRAFT": raise HTTPException(409,"Exam is locked")
    if not rows or len(rows)>5000: raise HTTPException(400,"Supply 1–5000 marks")
    for x in rows:
        if not d.query(Learner).filter_by(id=x.learner_id,school_id=u.school_id).first(): raise HTTPException(404,"Learner not found")
        if x.status not in ("ASSESSED","ABSENT","NOT_ASSESSED") or (x.status=="ASSESSED" and (x.score is None or not 0<=x.score<=x.maximum)) or (x.status!="ASSESSED" and x.score is not None): raise HTTPException(422,"Invalid mark or assessment status")
        subject=x.subject.strip().upper()
        if not subject: raise HTTPException(422,"Subject required")
        m=d.query(SubjectMark).filter_by(school_id=u.school_id,exam_id=eid,learner_id=x.learner_id,subject=subject).first()
        if not m:
            m=SubjectMark(school_id=u.school_id,exam_id=eid,learner_id=x.learner_id,subject=subject)
            d.add(m)
        m.score=x.score;m.maximum=x.maximum;m.status=x.status
    d.commit()
    return {"saved":len(rows)}
@app.get("/api/v1/analytics/{eid}")
def analytics(eid:str,d:Session=Depends(dbdep),u=Depends(staff)):
    e=exam_for(d,u,eid)
    rows=d.query(SubjectMark).filter_by(school_id=u.school_id,exam_id=eid).all()
    groups={}; learners={}
    for m in rows:
        if m.status!="ASSESSED": continue
        p=100*m.score/m.maximum
        groups.setdefault(m.subject,[]).append(p)
        learners.setdefault(m.learner_id,[]).append(p)
    mean=lambda a:round(sum(a)/len(a),2) if a else None
    return {"exam":e.title,"status":e.status,"subjects":[{"subject":k,"mean":mean(v),"assessed":len(v)} for k,v in sorted(groups.items())],"learners":[{"learner_id":k,"mean":mean(v),"assessed":len(v)} for k,v in learners.items()],"marks":[{"learner_id":m.learner_id,"subject":m.subject,"score":m.score,"maximum":m.maximum,"status":m.status} for m in rows],"missing":sum(m.status!="ASSESSED" for m in rows)}
