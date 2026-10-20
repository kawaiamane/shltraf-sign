import fnmatch, os, stat, zipfile, threading, time
from pathlib import Path, PurePosixPath

class Cancelled(Exception): pass

def safe_name(name):
    p=PurePosixPath(name.replace('\\','/'))
    return bool(name) and not p.is_absolute() and not any(x in ('..','') for x in p.parts) and not (len(name)>1 and name[1]==':')

def scan(root, excludes):
    root=Path(root).resolve()
    for base, dirs, files in os.walk(root, followlinks=False):
        rel=Path(base).relative_to(root)
        dirs[:]=[d for d in dirs if not Path(base,d).is_symlink() and not excluded((rel/d).as_posix(),excludes)]
        for f in files:
            p=Path(base,f)
            if p.is_symlink() or excluded((rel/f).as_posix(),excludes): continue
            if p.is_file(): yield p, (rel/f).as_posix(),p.stat().st_size

def excluded(path, patterns):
    return any(fnmatch.fnmatch(path,p) or any(fnmatch.fnmatch(part,p) for part in path.split('/')) for p in patterns)

def compress(job, source, target, level, excludes):
    source=Path(source).resolve(); target=Path(target).resolve()
    if not source.is_dir(): raise ValueError('Source must be a directory')
    if target.is_relative_to(source): raise ValueError('Output ZIP cannot be inside source directory')
    if source == target: raise ValueError('Invalid output')
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.partial')
    if temp.exists(): raise FileExistsError('Partial file already exists')
    try:
        job['phase']='scanning'
        # Scan once, retaining metadata rather than file contents.
        entries=list(scan(source,excludes))
        job['total_files']=len(entries);job['total_bytes']=sum(x[2] for x in entries)
        job['phase']='compressing'
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=level,allowZip64=True) as z:
            for p,rel,size in entries:
                if job['cancel'].is_set(): raise Cancelled()
                with p.open('rb') as inp,z.open(rel,'w',force_zip64=True) as out:
                    while True:
                        if job['cancel'].is_set(): raise Cancelled()
                        block=inp.read(1024*1024)
                        if not block: break
                        out.write(block);job['processed_bytes']+=len(block)
                job['processed_files']+=1
        if job['cancel'].is_set(): raise Cancelled()
        os.replace(temp,target);job['output']=str(target);job['output_bytes']=target.stat().st_size
    finally:
        if temp.exists(): temp.unlink()

def extract(job, source, dest, max_total=100*1024**3, max_files=1000000):
    source=Path(source).resolve(); dest=Path(dest).resolve()
    if not source.is_file(): raise ValueError('ZIP does not exist')
    if dest.exists() and any(dest.iterdir()): raise ValueError('Extraction destination must be empty')
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(source) as z:
        entries=z.infolist()
        if len(entries)>max_files or sum(i.file_size for i in entries)>max_total: raise ValueError('Archive exceeds safety limits')
        for i in entries:
            if not safe_name(i.filename): raise ValueError('Unsafe ZIP entry path')
            mode=(i.external_attr>>16)&0xffff
            if stat.S_ISLNK(mode): raise ValueError('ZIP symlinks are not supported')
        job['total_files']=sum(not i.is_dir() for i in entries)
        job['total_bytes']=sum(i.file_size for i in entries)
        job['phase']='extracting'
        for i in entries:
            if job['cancel'].is_set(): raise Cancelled()
            out=(dest/i.filename).resolve()
            if not out.is_relative_to(dest): raise ValueError('Unsafe extraction path')
            if i.is_dir(): out.mkdir(parents=True,exist_ok=True);continue
            out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(i) as inp,open(out,'xb') as f:
                while True:
                    if job['cancel'].is_set(): raise Cancelled()
                    chunk=inp.read(1024*1024)
                    if not chunk: break
                    f.write(chunk);job['processed_bytes']+=len(chunk)
            job['processed_files']+=1
    job['output']=str(dest)
