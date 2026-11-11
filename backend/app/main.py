from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, String, Integer, Boolean, Float, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from jose import jwt, JWTError
from pwdlib import PasswordHash

class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./jeztech_dev.db"
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    cors_origins: str = "http://localhost:5173"
    class Config: env_file = ".env"
settings=Settings()
db_url=settings.database_url
if db_url.startswith("postgres://"): db_url=db_url.replace("postgres://","postgresql+psycopg://",1)
elif db_url.startswith("postgresql://"): db_url=db_url.replace("postgresql://","postgresql+psycopg://",1)
connect_args={"check_same_thread":False} if db_url.startswith("sqlite") else {}
engine=create_engine(db_url,pool_pre_ping=True,connect_args=connect_args)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass

class School(Base):
    __tablename__="schools"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(180))
    code:Mapped[str]=mapped_column(String(40),unique=True,index=True)
    curriculum:Mapped[str]=mapped_column(String(20),default="CBC")
    county:Mapped[str|None]=mapped_column(String(80),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    full_name:Mapped[str]=mapped_column(String(160))
    email:Mapped[str]=mapped_column(String(254))
    password_hash:Mapped[str]=mapped_column(String(255))
    role:Mapped[str]=mapped_column(String(24),default="TEACHER")
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(UniqueConstraint("school_id","email",name="uq_user_school_email"),)
class ClassGroup(Base):
    __tablename__="classes"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    name:Mapped[str]=mapped_column(String(80))
    curriculum:Mapped[str]=mapped_column(String(20),default="CBC")
    stream:Mapped[str]=mapped_column(String(40),default="")
    __table_args__=(UniqueConstraint("school_id","name","stream",name="uq_class_stream"),)
class Learner(Base):
    __tablename__="learners"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    admission_number:Mapped[str]=mapped_column(String(50))
    first_name:Mapped[str]=mapped_column(String(80))
    last_name:Mapped[str]=mapped_column(String(80))
    gender:Mapped[str|None]=mapped_column(String(20),nullable=True)
    class_id:Mapped[int|None]=mapped_column(ForeignKey("classes.id"),nullable=True)
    status:Mapped[str]=mapped_column(String(20),default="ACTIVE")
    __table_args__=(UniqueConstraint("school_id","admission_number",name="uq_learner_admission"),)
class Subject(Base):
    __tablename__="subjects"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    code:Mapped[str]=mapped_column(String(30))
    name:Mapped[str]=mapped_column(String(100))
    curriculum:Mapped[str]=mapped_column(String(20),default="CBC")
    __table_args__=(UniqueConstraint("school_id","code",name="uq_subject_code"),)
class Exam(Base):
    __tablename__="exams"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    name:Mapped[str]=mapped_column(String(160))
    academic_year:Mapped[str]=mapped_column(String(20))
    term:Mapped[str]=mapped_column(String(30))
    exam_type:Mapped[str]=mapped_column(String(40),default="END_TERM")
    status:Mapped[str]=mapped_column(String(20),default="DRAFT")
class ExamPaper(Base):
    __tablename__="exam_papers"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    exam_id:Mapped[int]=mapped_column(ForeignKey("exams.id",ondelete="CASCADE"))
    subject_id:Mapped[int]=mapped_column(ForeignKey("subjects.id"))
    class_id:Mapped[int]=mapped_column(ForeignKey("classes.id"))
    max_score:Mapped[float]=mapped_column(Float,default=100)
    __table_args__=(UniqueConstraint("school_id","exam_id","subject_id","class_id",name="uq_exam_paper_scope"),)
class Mark(Base):
    __tablename__="marks"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    paper_id:Mapped[int]=mapped_column(ForeignKey("exam_papers.id",ondelete="CASCADE"),index=True)
    learner_id:Mapped[int]=mapped_column(ForeignKey("learners.id"),index=True)
    score:Mapped[float]=mapped_column(Float)
    entered_by:Mapped[int]=mapped_column(ForeignKey("users.id"))
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    __table_args__=(UniqueConstraint("school_id","paper_id","learner_id",name="uq_mark_learner_paper"),)
class GradeBand(Base):
    __tablename__="grade_bands"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    curriculum:Mapped[str]=mapped_column(String(20))
    label:Mapped[str]=mapped_column(String(30))
    minimum_percent:Mapped[float]=mapped_column(Float)
    maximum_percent:Mapped[float]=mapped_column(Float)
    points:Mapped[float|None]=mapped_column(Float,nullable=True)
    descriptor:Mapped[str|None]=mapped_column(String(120),nullable=True)
    __table_args__=(UniqueConstraint("school_id","curriculum","label",name="uq_grade_band_label"),)
class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[int]=mapped_column(primary_key=True)
    school_id:Mapped[int]=mapped_column(ForeignKey("schools.id",ondelete="CASCADE"),index=True)
    user_id:Mapped[int|None]=mapped_column(ForeignKey("users.id"),nullable=True)
    action:Mapped[str]=mapped_column(String(80))
    entity:Mapped[str]=mapped_column(String(80))
    entity_id:Mapped[str|None]=mapped_column(String(50),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

pwd=PasswordHash.recommended()
bearer=HTTPBearer(auto_error=False)
app=FastAPI(title="JEZTECH Intelligent Exam Analytics",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
def dbdep():
    db=SessionLocal()
    try: yield db
    finally: db.close()
def token_for(user):
    exp=datetime.now(timezone.utc)+timedelta(hours=8)
    return jwt.encode({"sub":str(user.id),"school_id":user.school_id,"role":user.role,"exp":exp},settings.jwt_secret,algorithm="HS256")
def current_user(auth:HTTPAuthorizationCredentials|None=Depends(bearer),db:Session=Depends(dbdep)):
    if not auth: raise HTTPException(401,"Sign in required")
    try: payload=jwt.decode(auth.credentials,settings.jwt_secret,algorithms=["HS256"]); uid=int(payload["sub"]); sid=int(payload["school_id"])
    except (JWTError,KeyError,ValueError,TypeError): raise HTTPException(401,"Session invalid or expired")
    user=db.query(User).filter_by(id=uid,school_id=sid,active=True).first()
    if not user: raise HTTPException(401,"Account unavailable")
    return user
def roles(*allowed):
    def guard(user:User=Depends(current_user)):
        if user.role not in allowed: raise HTTPException(403,"Permission denied")
        return user
    return guard
@app.on_event("startup")
def startup():
    if settings.environment=="development": Base.metadata.create_all(engine)
@app.get("/health")
def health(): return {"status":"ok","app":"jeztech-exam-analytics"}
class Register(BaseModel):
    school_name:str=Field(min_length=2,max_length=180)
    school_code:str=Field(min_length=2,max_length=40,pattern=r"^[A-Za-z0-9_-]+$")
    curriculum:str="CBC"
    county:str|None=None
    admin_name:str=Field(min_length=2,max_length=160)
    email:EmailStr
    password:str=Field(min_length=10,max_length=128)
class Login(BaseModel):
    school_code:str
    email:EmailStr
    password:str
class LearnerIn(BaseModel):
    admission_number:str
    first_name:str
    last_name:str
    gender:str|None=None
    class_id:int|None=None
class ClassIn(BaseModel):
    name:str
    curriculum:str="CBC"
    stream:str=""
class SubjectIn(BaseModel):
    code:str
    name:str
    curriculum:str="CBC"
class ExamIn(BaseModel):
    name:str
    academic_year:str
    term:str
    exam_type:str="END_TERM"
class PaperIn(BaseModel):
    subject_id:int
    class_id:int
    max_score:float=Field(gt=0,le=1000)
class MarkIn(BaseModel):
    learner_id:int
    score:float=Field(ge=0)
class MarkBatch(BaseModel):
    marks:list[MarkIn]=Field(min_length=1,max_length=1000)
@app.post("/api/auth/register",status_code=201)
def register(data:Register,db:Session=Depends(dbdep)):
    if db.query(School).filter(func.lower(School.code)==data.school_code.lower()).first(): raise HTTPException(409,"School code already registered")
    school=School(name=data.school_name.strip(),code=data.school_code.upper(),curriculum=data.curriculum,county=data.county)
    db.add(school);db.flush()
    user=User(school_id=school.id,full_name=data.admin_name.strip(),email=data.email.lower(),password_hash=pwd.hash(data.password),role="SCHOOL_ADMIN")
    db.add(user)
    try: db.commit()
    except IntegrityError: db.rollback();raise HTTPException(409,"School or administrator already exists")
    db.refresh(user)
    return {"access_token":token_for(user),"token_type":"bearer"}
@app.post("/api/auth/login")
def login(data:Login,db:Session=Depends(dbdep)):
    school=db.query(School).filter(func.lower(School.code)==data.school_code.lower()).first()
    user=db.query(User).filter_by(school_id=school.id,email=data.email.lower()).first() if school else None
    if not user or not user.active or not pwd.verify(data.password,user.password_hash): raise HTTPException(401,"School code, email or password is incorrect")
    return {"access_token":token_for(user),"token_type":"bearer"}
@app.get("/api/auth/me")
def me(user:User=Depends(current_user)): return {"id":user.id,"full_name":user.full_name,"email":user.email,"role":user.role}
@app.get("/api/school")
def school_info(db:Session=Depends(dbdep),user:User=Depends(current_user)):
    s=db.query(School).filter_by(id=user.school_id).first()
    return {"id":s.id,"name":s.name,"code":s.code,"curriculum":s.curriculum,"county":s.county}
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(dbdep),u:User=Depends(current_user)):
    sid=u.school_id
    return {"learners":db.query(Learner).filter_by(school_id=sid,status="ACTIVE").count(),"classes":db.query(ClassGroup).filter_by(school_id=sid).count(),"subjects":db.query(Subject).filter_by(school_id=sid).count(),"exams":db.query(Exam).filter_by(school_id=sid).count(),"marks":db.query(Mark).filter_by(school_id=sid).count()}
@app.get("/api/learners")
def learners(db:Session=Depends(dbdep),u:User=Depends(current_user)):
    return db.query(Learner).filter_by(school_id=u.school_id).order_by(Learner.admission_number).all()
@app.post("/api/learners",status_code=201)
def add_learner(data:LearnerIn,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS","SECRETARY"))):
    if data.class_id and not db.query(ClassGroup).filter_by(id=data.class_id,school_id=u.school_id).first(): raise HTTPException(404,"Class not found")
    row=Learner(school_id=u.school_id,**data.model_dump());db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError: db.rollback();raise HTTPException(409,"Admission number already exists")
    return row
@app.get("/api/classes")
def classes(db:Session=Depends(dbdep),u:User=Depends(current_user)): return db.query(ClassGroup).filter_by(school_id=u.school_id).all()
@app.post("/api/classes",status_code=201)
def add_class(data:ClassIn,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS"))):
    row=ClassGroup(school_id=u.school_id,**data.model_dump());db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError: db.rollback();raise HTTPException(409,"Class and stream already exist")
    return row
@app.get("/api/subjects")
def subjects(db:Session=Depends(dbdep),u:User=Depends(current_user)): return db.query(Subject).filter_by(school_id=u.school_id).all()
@app.post("/api/subjects",status_code=201)
def add_subject(data:SubjectIn,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS"))):
    row=Subject(school_id=u.school_id,**data.model_dump());db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError: db.rollback();raise HTTPException(409,"Subject code already exists")
    return row
@app.get("/api/exams")
def exams(db:Session=Depends(dbdep),u:User=Depends(current_user)): return db.query(Exam).filter_by(school_id=u.school_id).order_by(Exam.id.desc()).all()
@app.post("/api/exams",status_code=201)
def add_exam(data:ExamIn,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS"))):
    row=Exam(school_id=u.school_id,**data.model_dump());db.add(row);db.commit();db.refresh(row);return row
@app.post("/api/exams/{exam_id}/papers",status_code=201)
def add_paper(exam_id:int,data:PaperIn,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS"))):
    if not db.query(Exam).filter_by(id=exam_id,school_id=u.school_id).first(): raise HTTPException(404,"Exam not found")
    if not db.query(Subject).filter_by(id=data.subject_id,school_id=u.school_id).first(): raise HTTPException(404,"Subject not found")
    if not db.query(ClassGroup).filter_by(id=data.class_id,school_id=u.school_id).first(): raise HTTPException(404,"Class not found")
    row=ExamPaper(school_id=u.school_id,exam_id=exam_id,**data.model_dump());db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError: db.rollback();raise HTTPException(409,"Paper already mapped")
    return row
@app.put("/api/papers/{paper_id}/marks")
def save_marks(paper_id:int,data:MarkBatch,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS","TEACHER"))):
    paper=db.query(ExamPaper).filter_by(id=paper_id,school_id=u.school_id).first()
    if not paper: raise HTTPException(404,"Paper not found")
    ids=[m.learner_id for m in data.marks]
    if len(set(ids))!=len(ids): raise HTTPException(422,"Duplicate learner in marks batch")
    valid=db.query(Learner.id).filter(Learner.school_id==u.school_id,Learner.class_id==paper.class_id,Learner.status=="ACTIVE",Learner.id.in_(ids)).all()
    if len(valid)!=len(ids): raise HTTPException(422,"Every learner must be active and belong to this paper's class")
    if any(m.score>paper.max_score for m in data.marks): raise HTTPException(422,"Score exceeds maximum")
    for item in data.marks:
        row=db.query(Mark).filter_by(school_id=u.school_id,paper_id=paper.id,learner_id=item.learner_id).first()
        if row: row.score=item.score;row.entered_by=u.id
        else: db.add(Mark(school_id=u.school_id,paper_id=paper.id,learner_id=item.learner_id,score=item.score,entered_by=u.id))
    db.add(AuditLog(school_id=u.school_id,user_id=u.id,action="MARKS_SAVED",entity="EXAM_PAPER",entity_id=str(paper.id)))
    db.commit();return {"saved":len(ids)}
@app.get("/api/exams/{exam_id}/papers")
def papers(exam_id:int,db:Session=Depends(dbdep),u:User=Depends(current_user)):
    if not db.query(Exam).filter_by(id=exam_id,school_id=u.school_id).first(): raise HTTPException(404,"Exam not found")
    return db.query(ExamPaper).filter_by(school_id=u.school_id,exam_id=exam_id).all()
@app.get("/api/reports/exam/{exam_id}")
def report(exam_id:int,db:Session=Depends(dbdep),u:User=Depends(current_user)):
    exam=db.query(Exam).filter_by(id=exam_id,school_id=u.school_id).first()
    if not exam: raise HTTPException(404,"Exam not found")
    rows=db.query(Learner,Mark,ExamPaper,Subject,ClassGroup).join(Mark,Mark.learner_id==Learner.id).join(ExamPaper,ExamPaper.id==Mark.paper_id).join(Subject,Subject.id==ExamPaper.subject_id).join(ClassGroup,ClassGroup.id==Learner.class_id).filter(Mark.school_id==u.school_id,ExamPaper.exam_id==exam_id).all()
    output=[]
    for l,m,p,subject,c in rows:
        percent=round(m.score/p.max_score*100,2)
        band=db.query(GradeBand).filter(GradeBand.school_id==u.school_id,GradeBand.curriculum==subject.curriculum,GradeBand.minimum_percent<=percent,GradeBand.maximum_percent>=percent).first()
        output.append({"admission":l.admission_number,"learner":l.first_name+" "+l.last_name,"class":c.name,"subject":subject.name,"score":m.score,"maximum":p.max_score,"percent":percent,"grade":band.label if band else None,"grade_descriptor":band.descriptor if band else None})
    return output

@app.get("/api/papers/{paper_id}/marks")
def paper_marks(paper_id:int,db:Session=Depends(dbdep),u:User=Depends(current_user)):
    paper=db.query(ExamPaper).filter_by(id=paper_id,school_id=u.school_id).first()
    if not paper: raise HTTPException(404,"Paper not found")
    rows=db.query(Learner,Mark).outerjoin(Mark,(Mark.learner_id==Learner.id)&(Mark.paper_id==paper.id)&(Mark.school_id==u.school_id)).filter(Learner.school_id==u.school_id,Learner.class_id==paper.class_id,Learner.status=="ACTIVE").order_by(Learner.admission_number).all()
    return [{"learner_id":l.id,"admission_number":l.admission_number,"learner":l.first_name+" "+l.last_name,"score":m.score if m else None,"max_score":paper.max_score} for l,m in rows]

class GradeBandIn(BaseModel):
    curriculum:str=Field(pattern=r"^(CBC|844)$")
    label:str=Field(min_length=1,max_length=30)
    minimum_percent:float=Field(ge=0,le=100)
    maximum_percent:float=Field(ge=0,le=100)
    points:float|None=None
    descriptor:str|None=None

@app.get("/api/grade-bands")
def list_grade_bands(curriculum:str|None=None,db:Session=Depends(dbdep),u:User=Depends(current_user)):
    q=db.query(GradeBand).filter_by(school_id=u.school_id)
    if curriculum: q=q.filter_by(curriculum=curriculum)
    return q.order_by(GradeBand.curriculum,GradeBand.minimum_percent.desc()).all()

@app.post("/api/grade-bands",status_code=201)
def create_grade_band(data:GradeBandIn,db:Session=Depends(dbdep),u:User=Depends(roles("SCHOOL_ADMIN","PRINCIPAL","DOS"))):
    if data.minimum_percent>data.maximum_percent: raise HTTPException(422,"Minimum percentage cannot exceed maximum")
    overlap=db.query(GradeBand).filter(GradeBand.school_id==u.school_id,GradeBand.curriculum==data.curriculum,GradeBand.minimum_percent<=data.maximum_percent,GradeBand.maximum_percent>=data.minimum_percent).first()
    if overlap: raise HTTPException(409,"This percentage range overlaps an existing grade band")
    row=GradeBand(school_id=u.school_id,**data.model_dump());db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError: db.rollback();raise HTTPException(409,"Grade label already exists for this curriculum")
    return row
