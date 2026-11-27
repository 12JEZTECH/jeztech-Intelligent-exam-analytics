import io
from fastapi.responses import StreamingResponse
from .main import app,roles,Depends,dbdep,Session,HTTPException
from .exam_studio import GeneratedPaper
staff=roles("SCHOOL_ADMIN","TEACHER","DOS","PRINCIPAL")
@app.get("/api/v1/exam-studio/papers/{pid}/download")
def download(pid:str,format:str="pdf",scheme:bool=False,d:Session=Depends(dbdep),u=Depends(staff)):
    p=d.query(GeneratedPaper).filter_by(id=pid,school_id=u.school_id).first()
    if not p: raise HTTPException(404,"Paper not found")
    x=p.payload; title=x["subject"]+" - "+x["level"]+" - "+x["topic"]
    lines=[title,"Marking scheme" if scheme else "Question paper","Status: "+x["status"],"Total marks: "+str(sum(q["marks"] for q in x["questions"]))]
    for i,q in enumerate(x["questions"],1):
        lines.append(f"{i}. {q['prompt']} ({q['marks']} marks)")
        lines.extend(f"{chr(65+j)}. {o}" for j,o in enumerate(q["options"]))
        if scheme: lines.append("Answer: "+q["answer"])
    b=io.BytesIO()
    if format=="docx":
        from docx import Document
        doc=Document();doc.add_heading(lines[0],0)
        for line in lines[1:]: doc.add_paragraph(line)
        doc.save(b);mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif format=="pdf":
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from xml.sax.saxutils import escape
        styles=getSampleStyleSheet();story=[Paragraph(escape(lines[0]),styles["Title"])]
        for line in lines[1:]: story.extend([Paragraph(escape(line),styles["BodyText"]),Spacer(1,6)])
        SimpleDocTemplate(b).build(story);mime="application/pdf"
    else: raise HTTPException(422,"Use pdf or docx")
    b.seek(0);return StreamingResponse(b,media_type=mime,headers={"Content-Disposition":f"attachment; filename=exam-{'scheme' if scheme else 'paper'}.{format}"})
