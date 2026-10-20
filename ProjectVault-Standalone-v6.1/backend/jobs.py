import threading,uuid,time
from .core import Cancelled
from .pvx import compress, extract
class Manager:
    def __init__(self): self.jobs={};self.lock=threading.Lock()
    def start(self,kind,opts):
        with self.lock:
            if sum(j['phase'] not in ('done','failed','cancelled') for j in self.jobs.values())>=2: raise ValueError('At most two concurrent jobs')
            jid=uuid.uuid4().hex
            j=dict(id=jid,kind=kind,phase='queued',processed_files=0,total_files=0,processed_bytes=0,total_bytes=0,output=None,output_bytes=None,error=None,created=time.time(),cancel=threading.Event())
            self.jobs[jid]=j
        def run():
            try:
                if kind=='compress':compress(j,opts['source'],opts['target'],int(opts.get('level',6)),opts.get('excludes',[]))
                elif kind=='extract':extract(j,opts['source'],opts['target'])
                else: raise ValueError('Unknown operation')
                j['phase']='done'
            except Cancelled: j['phase']='cancelled'
            except Exception as e: j['error']=str(e);j['phase']='failed'
        threading.Thread(target=run,daemon=True).start()
        return self.status(jid)
    def status(self,jid):
        j=self.jobs.get(jid)
        if j is None: raise KeyError(jid)
        return {k:v for k,v in j.items() if k!='cancel'}
    def stop(self,jid):
        if jid not in self.jobs: raise KeyError(jid)
        self.jobs[jid]['cancel'].set()
        return self.status(jid)
