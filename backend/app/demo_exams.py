"""Demonstration assessment bank and deterministic marking."""
from .main import app, roles, Depends, HTTPException
from pydantic import BaseModel
BANK=[
{"id":"q1","subject":"Chemistry","kind":"MCQ","prompt":"Which apparatus measures a variable volume of solution during titration?","options":["Burette","Beaker","Tripod"],"answer":"Burette","marks":2},
{"id":"q2","subject":"Chemistry","kind":"NUMERIC","prompt":"Initial burette reading 0.50 mL; final reading 25.50 mL. Calculate titre in mL.","answer":25,"tolerance":0.05,"marks":3},
{"id":"q3","subject":"Chemistry","kind":"PRACTICAL","prompt":"Record your observations, procedure, calculations and conclusion for an acid-base titration.","marks":10},
{"id":"q4","subject":"Mathematics","kind":"NUMERIC","prompt":"Solve 3x + 5 = 20.","answer":5,"tolerance":0.001,"marks":2},
{"id":"q5","subject":"Mathematics","kind":"MCQ","prompt":"What is the area of a rectangle 8 cm by 4 cm?","options":["12","24","32"],"answer":"32","marks":2}]
@app.get("/api/v1/demo-exams")
def demo_exams(subject:str="Chemistry",u=Depends(roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL","STUDENT"))):
    return {"demo":True,"questions":[{k:v for k,v in q.items() if k not in ("answer","tolerance")} for q in BANK if q["subject"]==subject]}
class Submission(BaseModel):
    subject:str
    answers:dict
@app.post("/api/v1/demo-exams/mark")
def demo_mark(x:Submission,u=Depends(roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL","STUDENT"))):
    results=[]
    for q in BANK:
        if q["subject"]!=x.subject: continue
        a=x.answers.get(q["id"])
        if q["kind"]=="PRACTICAL":
            results.append({"id":q["id"],"awarded":None,"maximum":q["marks"],"status":"TEACHER_REVIEW","submitted":bool(a)});continue
        if q["kind"]=="NUMERIC":
            try: correct=abs(float(a)-q["answer"])<=q["tolerance"]
            except (ValueError,TypeError): correct=False
        else: correct=a==q["answer"]
        results.append({"id":q["id"],"awarded":q["marks"] if correct else 0,"maximum":q["marks"],"status":"MARKED"})
    return {"demo":True,"results":results,"score":sum(r["awarded"] or 0 for r in results),"marked_maximum":sum(r["maximum"] for r in results if r["awarded"] is not None)}
@app.get("/api/v1/demo-exams/scheme")
def scheme(subject:str="Chemistry",u=Depends(roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL"))):
    return {"demo":True,"questions":[q for q in BANK if q["subject"]==subject]}
