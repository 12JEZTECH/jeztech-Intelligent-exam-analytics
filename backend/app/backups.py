"""School-scoped downloadable data backup, including binary evidence."""
import io,json,base64,zipfile,datetime
from sqlalchemy import select
from fastapi.responses import StreamingResponse
from .main import app,Base,dbdep,roles,Depends,Session
@app.get("/api/v1/backups/school")
def backup(d:Session=Depends(dbdep),u=Depends(roles("SCHOOL_ADMIN"))):
    tables=Base.metadata.tables
    result={}
    def encode(v):
        if isinstance(v,bytes):return {"encoding":"base64","data":base64.b64encode(v).decode()}
        return str(v)
    for name,t in tables.items():
        if "school_id" in t.c: q=select(t).where(t.c.school_id==u.school_id)
        elif name=="schools":q=select(t).where(t.c.id==u.school_id)
        elif name=="learning_work_evidence":q=select(t).where(t.c.work_id.in_(select(tables["learning_work_submissions"].c.id).where(tables["learning_work_submissions"].c.school_id==u.school_id)))
        elif name=="exam_questions":q=select(t).where(t.c.exam_id.in_(select(tables["exams"].c.id).where(tables["exams"].c.school_id==u.school_id)))
        elif name=="answers":q=select(t).where(t.c.attempt_id.in_(select(tables["attempts"].c.id).where(tables["attempts"].c.school_id==u.school_id)))
        else:continue
        result[name]=[{k:v for k,v in row.items() if k!="password_hash"} for row in d.execute(q).mappings()]
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json",json.dumps({"school_id":u.school_id,"created":datetime.datetime.now(datetime.timezone.utc).isoformat(),"type":"school-data-export","passwords_excluded":True,"counts":{k:len(v) for k,v in result.items()}}))
        for name,rows in result.items():z.writestr(name+".json",json.dumps(rows,default=encode))
    b.seek(0)
    return StreamingResponse(b,media_type="application/zip",headers={"Content-Disposition":"attachment; filename=jeztech-school-backup.zip","Cache-Control":"no-store"})
