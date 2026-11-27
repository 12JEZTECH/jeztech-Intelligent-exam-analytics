from .main import app,roles,Depends,dbdep,Session,AcademicClass,HTTPException,BaseModel,Field
staff=roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL")
class ClassInput(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    curriculum:str="CBC"
@app.get("/api/v1/school/classes")
def classes(d:Session=Depends(dbdep),u=Depends(staff)):
    return [{"id":c.id,"name":c.name,"curriculum":c.curriculum} for c in d.query(AcademicClass).filter_by(school_id=u.school_id)]
@app.post("/api/v1/school/classes")
def create_class(x:ClassInput,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","DOS"))):
    if x.curriculum not in ("CBC","844"): raise HTTPException(422,"Invalid curriculum")
    if d.query(AcademicClass).filter_by(school_id=u.school_id,name=x.name).first(): raise HTTPException(409,"Class exists")
    c=AcademicClass(school_id=u.school_id,**x.model_dump());d.add(c);d.commit();return {"id":c.id}
