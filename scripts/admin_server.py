#!/usr/bin/env python3
import base64, http.server, json, os, sqlite3, sys, uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--port' else 8499
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, '..', 'backend', 'RajibLabs.Api', 'rajiblabs.db')
USER = os.environ.get('ADMIN_USER', 'rajib')
PASS = os.environ.get('ADMIN_PASSWORD', 'rajiblabs2026')

def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS Contacts(Id TEXT PRIMARY KEY, Name TEXT, Email TEXT, Company TEXT, Message TEXT, SubmittedAt TEXT);
        CREATE TABLE IF NOT EXISTS Subscribers(Id TEXT PRIMARY KEY, Email TEXT UNIQUE, IsActive INTEGER DEFAULT 1, SubscribedAt TEXT, UnsubscribedAt TEXT);
        CREATE TABLE IF NOT EXISTS LinkedInCourses(Id TEXT PRIMARY KEY, Title TEXT, Url TEXT, Instructor TEXT, Duration TEXT, Level TEXT, CompletedAt TEXT, Status TEXT DEFAULT 'in-progress', UpdatedAt TEXT);
    """)
    c.commit(); c.close()

def q(sql, par=()):
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    r = [dict(x) for x in c.execute(sql, par).fetchall()]; c.close(); return r

def ex(sql, par=()):
    c = sqlite3.connect(DB); c.execute(sql, par); c.commit(); c.close()

def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

CSS = "body{font-family:system-ui,-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;margin:0}nav{background:#1e293b;border-bottom:1px solid #334155;padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}nav a{color:#94a3b8;text-decoration:none;font-size:13px;padding:6px 10px;border-radius:6px}nav a:hover,nav a.sel{color:#fff;background:#1d4ed8}nav .brand{font-weight:700;color:#fff;margin-right:auto}.stats{display:flex;gap:12px;padding:20px 24px;flex-wrap:wrap}.card{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:16px 20px;flex:1;min-width:150px}.card .v{font-size:28px;font-weight:700;color:#60a5fa}.card .l{font-size:12px;color:#64748b;margin-top:2px}.main{padding:0 24px 24px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:8px 10px;border-bottom:1px solid #1e293b}th{color:#64748b;font-weight:600;font-size:11px;text-transform:uppercase}tr:hover{background:#1e293b}.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}.bg{background:#065f46;color:#6ee7b7}.br{background:#7f1d1d;color:#fca5a5}.empty{color:#64748b;padding:32px;text-align:center}a.ext{color:#60a5fa}"

HEAD = '<!DOCTYPE html><html lang=en><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1"><title>RajibLabs Admin</title><style>'+CSS+'</style>'
NAV = '<nav><b class=brand>RajibLabs Admin</b><a href="?s=dash">Dashboard</a><a href="?s=contacts">Contacts ({c})</a><a href="?s=subs">Subscribers ({a})</a><a href="?s=learn">Learning ({l})</a><a href="?logout=1" style=color:#ef4444>Logout</a></nav>'

def page(s='dash'):
    contacts=q('SELECT * FROM Contacts ORDER BY SubmittedAt DESC')
    subs=q('SELECT * FROM Subscribers ORDER BY SubscribedAt DESC')
    active=[x for x in subs if x.get('IsActive')]
    courses=q('SELECT * FROM LinkedInCourses ORDER BY UpdatedAt DESC')
    nav=NAV.format(c=len(contacts),a=len(active),l=len(courses))
    stats=f'<div class=stats><div class=card><div class=v>{len(contacts)}</div><div class=l>Messages</div></div><div class=card><div class=v>{len(active)}</div><div class=l>Subscribers</div></div><div class=card><div class=v>{len(courses)}</div><div class=l>Courses</div></div></div>'
    if s=='contacts':
        body='<div class=main><h3>Contact Messages</h3>'
        if not contacts: body+='<div class=empty>No messages yet. Form is live at rajiblabs.com</div>'
        else:
            body+='<table><tr><th>Date</th><th>Name</th><th>Email</th><th>Company</th><th>Message</th></tr>'
            for x in contacts:
                dt=(x.get('SubmittedAt') or'')[:16].replace('T',' ')
                body+=f'<tr><td>{dt}</td><td>{x.get("Name","")}</td><td>{x.get("Email","")}</td><td>{x.get("Company") or "-"}</td><td style=max-width:300px;word-break:break-word>{x.get("Message","")[:200]}</td></tr>'
            body+='</table>'
        body+='</div>'
    elif s=='subs':
        body='<div class=main><h3>Subscribers</h3>'
        if not subs: body+='<div class=empty>No subscribers yet.</div>'
        else:
            body+='<table><tr><th>Date</th><th>Email</th><th>Status</th></tr>'
            for x in subs:
                dt=(x.get('SubscribedAt') or'')[:10]
                st,bc=('Active','bg') if x.get('IsActive') else ('Unsubscribed','br')
                body+=f'<tr><td>{dt}</td><td>{x["Email"]}</td><td><span class="badge {bc}">{st}</span></td></tr>'
            body+='</table>'
        body+='</div>'
    elif s=='learn':
        body='<div class=main><h3>LinkedIn Learning</h3>'
        if not courses: body+='<div class=empty>No courses synced.</div>'
        else:
            body+='<table><tr><th>Status</th><th>Course</th><th>Instructor</th><th>Level</th><th>Duration</th></tr>'
            for x in courses:
                st='In Progress' if x.get('Status')=='in-progress' else 'Completed'
                url=x.get('Url','#')
                body+=f'<tr><td>{st}</td><td><a class=ext href="{url}">{x["Title"]}</a></td><td>{x.get("Instructor") or "-"}</td><td>{x.get("Level") or "-"}</td><td>{x.get("Duration") or "-"}</td></tr>'
            body+='</table>'
        body+='</div>'
    else:
        body='<div class=main><p class=empty>Select a section above to view data.</p></div>'
    return HEAD+nav+stats+body+'</html>'

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs=parse_qs(urlparse(self.path).query)
        if 'logout' in qs:
            self.send_response(401); self.send_header('WWW-Authenticate','Basic realm="RajibLabs"'); self.end_headers(); return
        a=self.headers.get('Authorization','')
        if not a:
            self.send_response(401); self.send_header('WWW-Authenticate','Basic realm="RajibLabs"'); self.end_headers(); return
        try:
            _,d=a.split(' ',1); u,_,p=base64.b64decode(d).decode().partition(':')
            if u!=USER or p!=PASS: raise ValueError
        except:
            self.send_response(403); self.end_headers(); return
        s=qs.get('s',['dash'])[0]
        h=page(s).encode()
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(h)
    def do_POST(self):
        p=urlparse(self.path).path
        n=int(self.headers.get('Content-Length',0))
        b=json.loads(self.rfile.read(n)) if n else {}
        if p=='/api/subscribe':
            e=(b.get('email','') or'').strip().lower()
            if not e or '@' not in e: self.json(400,{'error':'Valid email required'}); return
            old=q('SELECT * FROM Subscribers WHERE Email=?',(e,))
            if old:
                if not old[0].get('IsActive'): ex('UPDATE Subscribers SET IsActive=1,SubscribedAt=?,UnsubscribedAt=NULL WHERE Email=?',(now(),e)); self.json(200,{'message':'Welcome back!'}); return
                self.json(200,{'message':'Already subscribed!'}); return
            ex('INSERT INTO Subscribers(Id,Email,SubscribedAt) VALUES(?,?,?)',(str(uuid.uuid4()),e,now()))
            self.json(201,{'message':'Subscribed!'})
        elif p=='/api/contact':
            nm=(b.get('name','')or'').strip(); em=(b.get('email','')or'').strip(); ms=(b.get('message','')or'').strip(); co=(b.get('company','')or'').strip() or None
            if not nm or not em or not ms: self.json(400,{'error':'Name, email, message required'}); return
            ex('INSERT INTO Contacts(Id,Name,Email,Company,Message,SubmittedAt) VALUES(?,?,?,?,?,?)',(str(uuid.uuid4()),nm,em,co,ms,now()))
            self.json(201,{'id':str(uuid.uuid4())[:8],'message':'Message received!'})
        else: self.json(404,{'error':'Not found'})
    def json(self,code,data):
        self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(json.dumps(data).encode())
    def do_OPTIONS(self):
        self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type,Authorization'); self.end_headers()
    def log_message(self,*a): pass

if __name__=='__main__':
    init_db()
    print(f'Admin: http://localhost:{PORT}/admin  |  User: {USER}  Pass: {PASS}')
    http.server.HTTPServer(('127.0.0.1',PORT),H).serve_forever()
