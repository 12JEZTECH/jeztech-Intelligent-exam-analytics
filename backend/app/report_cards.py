from .main import app,dbdep,roles,Depends,HTTPException,Session,Exam,Learner
from .analytics import SubjectMark
from .grading import GradePolicy
from .academic_management import AcademicRecord
@app.get("/api/v1/report-cards/{eid}/{lid}")
def card(eid:str,lid:str,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL","PARENT"))):
    e=d.query(Exam).filter_by(id=eid,school_id=u.school_id).first()
    l=d.query(Learner).filter_by(id=lid,school_id=u.school_id).first()
    if not e or not l:raise HTTPException(404,"Not found")
    if u.role=="PARENT":
        if e.status!="PUBLISHED" or not d.query(AcademicRecord).filter_by(school_id=u.school_id,kind="parent",key=u.id+":"+lid).first():raise HTTPException(404,"Report unavailable")
    p=d.get(GradePolicy,(u.school_id,e.curriculum))
    rows=[]
    for m in d.query(SubjectMark).filter_by(school_id=u.school_id,exam_id=eid,learner_id=lid):
        percent=round(100*m.score/m.maximum,2) if m.status=="ASSESSED" else None
        grade=next((b for b in p.boundaries if percent>=b["minimum"]),None) if p and percent is not None else None
        rows.append({"subject":m.subject,"percentage":percent,"grade":grade["label"] if grade else None,"points":grade["points"] if grade else None,"status":m.status})
    scores=[r["percentage"] for r in rows if r["percentage"] is not None]
    return {"learner":l.first_name+" "+l.last_name,"admission":l.admission_number,"exam":e.title,"status":e.status,"subjects":rows,"mean":round(sum(scores)/len(scores),2) if scores else None,"policy_configured":bool(p)}
@app.get("/api/v1/report-cards/parent/exams/list")
def parent_exams(d:Session=Depends(dbdep),u=Depends(roles("PARENT"))):
    return [{"id":e.id,"title":e.title} for e in d.query(Exam).filter_by(school_id=u.school_id,status="PUBLISHED")]
