import os,csv,io,uuid
from fastapi import FastAPI,Depends,HTTPException,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel,Field
from sqlalchemy import create_engine,String,Text,Boolean,Float,ForeignKey,JSON
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker,Session
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
DB=os.getenv("DATABASE_URL","sqlite:///./jeztech.db"); engine=create_engine(DB,connect_args={"check_same_thread":False} if DB.startswith("sqlite") else {},pool_pre_ping=True); SessionLocal=sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
def uid(): return str(uuid.uuid4())
class School(Base):
 __tablename__="schools"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); name:Mapped[str]=mapped_column(String(200)); code:Mapped[str]=mapped_column(String(50),unique=True)
class User(Base):
 __tablename__="users"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id")); name:Mapped[str]=mapped_column(String(200)); email:Mapped[str]=mapped_column(String(200),unique=True); password_hash:Mapped[str]=mapped_column(String(255)); role:Mapped[str]=mapped_column(String(30),default="SCHOOL_ADMIN")
class Learner(Base):
 __tablename__="learners"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id"),index=True); admission_number:Mapped[str]=mapped_column(String(60)); first_name:Mapped[str]=mapped_column(String(100)); last_name:Mapped[str]=mapped_column(String(100),default=""); gender:Mapped[str]=mapped_column(String(20),default=""); guardian_phone:Mapped[str]=mapped_column(String(40),default="")
class AcademicClass(Base):
 __tablename__="classes"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id")); name:Mapped[str]=mapped_column(String(100)); curriculum:Mapped[str]=mapped_column(String(10),default="CBC")
class Exam(Base):
 __tablename__="exams"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id")); title:Mapped[str]=mapped_column(String(200)); curriculum:Mapped[str]=mapped_column(String(10)); duration:Mapped[float]=mapped_column(Float,default=60); status:Mapped[str]=mapped_column(String(20),default="DRAFT")
class Question(Base):
 __tablename__="questions"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id"),index=True); curriculum:Mapped[str]=mapped_column(String(10)); subject:Mapped[str]=mapped_column(String(120)); topic:Mapped[str]=mapped_column(String(200),default=""); kind:Mapped[str]=mapped_column(String(30)); prompt:Mapped[str]=mapped_column(Text); options:Mapped[list|None]=mapped_column(JSON,nullable=True); answer_key:Mapped[dict|None]=mapped_column(JSON,nullable=True); marks:Mapped[float]=mapped_column(Float,default=1); approved:Mapped[bool]=mapped_column(Boolean,default=False)
class ExamQuestion(Base):
 __tablename__="exam_questions"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); exam_id:Mapped[str]=mapped_column(ForeignKey("exams.id")); question_id:Mapped[str]=mapped_column(ForeignKey("questions.id"))
class Attempt(Base):
 __tablename__="attempts"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); exam_id:Mapped[str]=mapped_column(ForeignKey("exams.id")); learner_id:Mapped[str]=mapped_column(ForeignKey("learners.id")); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id")); status:Mapped[str]=mapped_column(String(30),default="IN_PROGRESS"); score:Mapped[float]=mapped_column(Float,default=0); maximum:Mapped[float]=mapped_column(Float,default=0)
class Answer(Base):
 __tablename__="answers"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); attempt_id:Mapped[str]=mapped_column(ForeignKey("attempts.id")); question_id:Mapped[str]=mapped_column(ForeignKey("questions.id")); response:Mapped[dict]=mapped_column(JSON); awarded:Mapped[float|None]=mapped_column(Float,nullable=True)
class Assignment(Base):
 __tablename__="assignments"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id")); title:Mapped[str]=mapped_column(String(200)); category:Mapped[str]=mapped_column(String(30)); description:Mapped[str]=mapped_column(Text,default="")
class Message(Base):
 __tablename__="messages"; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid); school_id:Mapped[str]=mapped_column(ForeignKey("schools.id")); channel:Mapped[str]=mapped_column(String(20)); recipient:Mapped[str]=mapped_column(String(80)); body:Mapped[str]=mapped_column(Text); status:Mapped[str]=mapped_column(String(20),default="QUEUED")
Base.metadata.create_all(engine)
def dbdep():
 d=SessionLocal()
 try: yield d
 finally: d.close()
SECRET=os.getenv("APP_SECRET","unsafe-dev-secret-change-me"); pwd=CryptContext(schemes=["bcrypt"],deprecated="auto"); oauth=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
def make_token(u): return jwt.encode({"sub":u.id,"school":u.school_id,"role":u.role},SECRET,algorithm="HS256")
def current(t:str=Depends(oauth),db:Session=Depends(dbdep)):
 try: p=jwt.decode(t,SECRET,algorithms=["HS256"]); u=db.get(User,p["sub"])
 except Exception: u=None
 if not u: raise HTTPException(401,"Invalid session")
 return u
def roles(*allowed):
 def check(u=Depends(current)):
  if u.role not in allowed: raise HTTPException(403,"Not permitted")
  return u
 return check
app=FastAPI(title="JEZTECH Academic Intelligence",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:5173").split(","),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
class Register(BaseModel):
 school_name:str; school_code:str; name:str; email:str; password:str=Field(min_length=10); curriculum:str="CBC"
class Login(BaseModel): email:str; password:str
class LearnerIn(BaseModel): admission_number:str; first_name:str; last_name:str=""; gender:str=""; guardian_phone:str=""
class ExamIn(BaseModel): title:str; curriculum:str; duration:int=Field(60,ge=1,le=360)
class QuestionIn(BaseModel):
 curriculum:str; subject:str; topic:str=""; kind:str="MCQ"; prompt:str; options:list|None=None; answer_key:dict|None=None; marks:float=Field(1,gt=0)
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/v1/auth/register")
def register(x:Register,d:Session=Depends(dbdep)):
 if os.getenv("APP_ENV")=="production": raise HTTPException(403,"Use secure administrator provisioning in production")
 if d.query(User).filter_by(email=x.email).first(): raise HTTPException(409,"Email exists")
 s=School(name=x.school_name,code=x.school_code); d.add(s); d.flush(); u=User(school_id=s.id,name=x.name,email=x.email,password_hash=pwd.hash(x.password),role="SCHOOL_ADMIN"); d.add(u); d.commit()
 return {"access_token":make_token(u),"user":{"name":u.name,"role":u.role}}
@app.post("/api/v1/auth/token")
def login(x:Login,d:Session=Depends(dbdep)):
 u=d.query(User).filter_by(email=x.email).first()
 if not u or not pwd.verify(x.password,u.password_hash): raise HTTPException(401,"Incorrect login")
 return {"access_token":make_token(u),"user":{"name":u.name,"role":u.role}}
@app.get("/api/v1/me")
def me(u=Depends(current)): return {"id":u.id,"school_id":u.school_id,"name":u.name,"role":u.role}
@app.get("/api/v1/dashboard")
def dashboard(d:Session=Depends(dbdep),u=Depends(current)):
 s=u.school_id; return {"learners":d.query(Learner).filter_by(school_id=s).count(),"exams":d.query(Exam).filter_by(school_id=s).count(),"questions":d.query(Question).filter_by(school_id=s).count(),"assignments":d.query(Assignment).filter_by(school_id=s).count()}
@app.get("/api/v1/learners")
def learners(d:Session=Depends(dbdep),u=Depends(current)):
 return [dict(id=x.id,admission_number=x.admission_number,first_name=x.first_name,last_name=x.last_name,gender=x.gender,guardian_phone=x.guardian_phone) for x in d.query(Learner).filter_by(school_id=u.school_id).all()]
@app.post("/api/v1/learners")
def add_learner(x:LearnerIn,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","TEACHER"))):
 if d.query(Learner).filter_by(school_id=u.school_id,admission_number=x.admission_number).first(): raise HTTPException(409,"Duplicate admission number")
 y=Learner(school_id=u.school_id,**x.model_dump()); d.add(y); d.commit(); return {"id":y.id}
@app.post("/api/v1/learners/import")
async def import_learners(file:UploadFile=File(...),d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN"))):
 from openpyxl import load_workbook
 raw=await file.read(); nm=(file.filename or "").lower()
 if nm.endswith(".csv"): rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
 elif nm.endswith(".xlsx"):
  ws=load_workbook(io.BytesIO(raw),read_only=True,data_only=True).active; vals=list(ws.values); heads=[str(v).strip().lower() for v in vals[0]]; rows=[dict(zip(heads,r)) for r in vals[1:] if any(r)]
 else: raise HTTPException(400,"CSV/XLSX supported. PDF scan extraction requires OCR verification.")
 good=0; errs=[]
 for i,r in enumerate(rows,2):
  a=str(r.get("admission_number",r.get("admission no","")) or "").strip(); n=str(r.get("first_name",r.get("name","")) or "").strip()
  if not a or not n: errs.append({"row":i,"error":"admission_number and first_name required"}); continue
  if d.query(Learner).filter_by(school_id=u.school_id,admission_number=a).first(): errs.append({"row":i,"error":"duplicate"}); continue
  d.add(Learner(school_id=u.school_id,admission_number=a,first_name=n,last_name=str(r.get("last_name","") or ""))); good+=1
 d.commit(); return {"created":good,"failed":len(errs),"errors":errs[:100]}
@app.get("/api/v1/exams")
def exams(d:Session=Depends(dbdep),u=Depends(current)): return [dict(id=x.id,title=x.title,curriculum=x.curriculum,duration=x.duration,status=x.status) for x in d.query(Exam).filter_by(school_id=u.school_id).all()]
@app.post("/api/v1/exams")
def add_exam(x:ExamIn,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","TEACHER"))):
 y=Exam(school_id=u.school_id,**x.model_dump()); d.add(y); d.commit(); return {"id":y.id}
@app.get("/api/v1/questions")
def questions(d:Session=Depends(dbdep),u=Depends(current)): return [dict(id=q.id,prompt=q.prompt,kind=q.kind,subject=q.subject,curriculum=q.curriculum,marks=q.marks,approved=q.approved) for q in d.query(Question).filter_by(school_id=u.school_id).all()]
@app.post("/api/v1/questions")
def add_question(x:QuestionIn,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","TEACHER"))):
 y=Question(school_id=u.school_id,approved=False,**x.model_dump()); d.add(y); d.commit(); return {"id":y.id,"status":"PENDING_REVIEW"}
@app.post("/api/v1/questions/{qid}/approve")
def approve(qid:str,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN"))):
 q=d.query(Question).filter_by(id=qid,school_id=u.school_id).first()
 if not q: raise HTTPException(404,"Not found")
 q.approved=True; d.commit(); return {"approved":True}
@app.post("/api/v1/exams/{eid}/attach/{qid}")
def attach(eid:str,qid:str,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","TEACHER"))):
 e=d.query(Exam).filter_by(id=eid,school_id=u.school_id).first(); q=d.query(Question).filter_by(id=qid,school_id=u.school_id,approved=True).first()
 if not e or not q: raise HTTPException(404,"Exam or approved question not found")
 d.add(ExamQuestion(exam_id=eid,question_id=qid)); d.commit(); return {"attached":True}
@app.post("/api/v1/exams/{eid}/publish")
def publish(eid:str,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN"))):
 e=d.query(Exam).filter_by(id=eid,school_id=u.school_id).first()
 if not e: raise HTTPException(404,"Exam not found")
 e.status="PUBLISHED"; d.commit(); return {"status":e.status}
@app.post("/api/v1/exams/{eid}/attempts/{learner_id}")
def start(eid:str,learner_id:str,d:Session=Depends(dbdep),u=Depends(current)):
 e=d.query(Exam).filter_by(id=eid,school_id=u.school_id,status="PUBLISHED").first(); l=d.query(Learner).filter_by(id=learner_id,school_id=u.school_id).first()
 if not e or not l: raise HTTPException(404,"Exam or learner not found")
 a=Attempt(exam_id=eid,learner_id=learner_id,school_id=u.school_id); d.add(a); d.commit(); return {"attempt_id":a.id}
@app.get("/api/v1/attempts/{aid}/paper")
def paper(aid:str,d:Session=Depends(dbdep),u=Depends(current)):
 a=d.query(Attempt).filter_by(id=aid,school_id=u.school_id).first()
 if not a: raise HTTPException(404,"Attempt not found")
 out=[]
 for x in d.query(ExamQuestion).filter_by(exam_id=a.exam_id):
  q=d.get(Question,x.question_id); out.append(dict(id=q.id,prompt=q.prompt,kind=q.kind,options=q.options,marks=q.marks))
 return out
@app.post("/api/v1/attempts/{aid}/answer/{qid}")
def answer(aid:str,qid:str,data:dict,d:Session=Depends(dbdep),u=Depends(current)):
 a=d.query(Attempt).filter_by(id=aid,school_id=u.school_id,status="IN_PROGRESS").first()
 if not a: raise HTTPException(404,"Attempt not active")
 old=d.query(Answer).filter_by(attempt_id=aid,question_id=qid).first()
 if old: old.response=data
 else: d.add(Answer(attempt_id=aid,question_id=qid,response=data))
 d.commit(); return {"saved":True}
@app.post("/api/v1/attempts/{aid}/submit")
def submit(aid:str,d:Session=Depends(dbdep),u=Depends(current)):
 a=d.query(Attempt).filter_by(id=aid,school_id=u.school_id,status="IN_PROGRESS").first()
 if not a: raise HTTPException(404,"Attempt not active")
 score=0; maximum=0; manual=False
 for x in d.query(ExamQuestion).filter_by(exam_id=a.exam_id):
  q=d.get(Question,x.question_id); maximum+=q.marks; ans=d.query(Answer).filter_by(attempt_id=aid,question_id=q.id).first()
  if not ans: continue
  if q.kind in ("MCQ","TRUE_FALSE","FILL_BLANK"):
   key=(q.answer_key or {}).get("answer"); actual=(ans.response or {}).get("answer"); accepted=(q.answer_key or {}).get("accepted",[])
   ans.awarded=q.marks if actual==key or actual in accepted else 0; score+=ans.awarded
  else: manual=True
 a.score=score; a.maximum=maximum; a.status="REVIEW_REQUIRED" if manual else "MARKED"; d.commit()
 return {"score":score,"maximum":maximum,"status":a.status,"manual_review":manual}
@app.get("/api/v1/assignments")
def assignments(d:Session=Depends(dbdep),u=Depends(current)): return [dict(id=x.id,title=x.title,category=x.category,description=x.description) for x in d.query(Assignment).filter_by(school_id=u.school_id)]
@app.post("/api/v1/assignments")
def add_assignment(data:dict,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN","TEACHER"))):
 x=Assignment(school_id=u.school_id,title=data["title"],category=data.get("category","HOMEWORK"),description=data.get("description","")); d.add(x); d.commit(); return {"id":x.id}
@app.post("/api/v1/communications/queue")
def queue(data:dict,d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN"))):
 ch=data.get("channel","SMS").upper()
 if ch not in ("SMS","WHATSAPP"): raise HTTPException(400,"Invalid channel")
 m=Message(school_id=u.school_id,channel=ch,recipient=data["recipient"],body=data["body"]); d.add(m); d.commit(); return {"id":m.id,"status":"QUEUED"}
@app.get("/api/v1/reports/learners.csv")
def export(d:Session=Depends(dbdep),u=Depends(current)):
 st=io.StringIO(); w=csv.writer(st); w.writerow(["Admission","First name","Last name","Gender","Phone"])
 for x in d.query(Learner).filter_by(school_id=u.school_id): w.writerow([x.admission_number,x.first_name,x.last_name,x.gender,x.guardian_phone])
 return StreamingResponse(iter([st.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=learners.csv"})
@app.post("/api/v1/ai/questions/generate")
def generate(data:dict,u=Depends(roles("SCHOOL_ADMIN","TEACHER"))):
 return {"configured":False,"message":"Configure an approved AI API adapter and server-side key; all generated questions require teacher review.","prompt_preview":f"Generate {data.get('count',10)} questions for {data.get('curriculum')} {data.get('level')} {data.get('subject')} on {data.get('topic')}."}
