"""PVX v1: original streaming container, independently specified. Not ZIP compatible."""
import os, json, zlib, struct, hashlib, fnmatch
from pathlib import Path, PurePosixPath
from .core import scan, Cancelled, safe_name

MAGIC=b"PVXARCH\x00"; VERSION=1; CHUNK=1024*1024
# magic(8), version(u16), chunk_size(u32), followed by records:
# F: metadata length(u32), JSON {path,size}; then repeated
# C: raw_size(u32), compressed_size(u32), sha256(32), compressed bytes
# E: terminates file; Z: terminates archive. All integers big endian.
def exact(f,n):
    b=f.read(n)
    if len(b)!=n:raise ValueError("Truncated PVX archive")
    return b
def num(f,n):f.write(struct.pack('>I',n))
def getnum(f):return struct.unpack('>I',exact(f,4))[0]
def compress(job,source,target,level,excludes):
    source=Path(source).resolve();target=Path(target).resolve()
    if not source.is_dir():raise ValueError('Source must be a directory')
    if target.is_relative_to(source):raise ValueError('Archive must be outside source')
    if not 0<=level<=9:raise ValueError('Invalid level')
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.partial')
    entries=list(scan(source,excludes))
    job.update(phase='compressing',total_files=len(entries),total_bytes=sum(x[2] for x in entries))
    try:
        with temp.open('xb') as out:
            out.write(MAGIC);out.write(struct.pack('>HI',VERSION,CHUNK))
            for path,rel,size in entries:
                if job['cancel'].is_set():raise Cancelled()
                meta=json.dumps({'path':rel,'size':size},ensure_ascii=False,separators=(',',':')).encode('utf-8')
                if len(meta)>65536:raise ValueError('File name too long')
                out.write(b'F');num(out,len(meta));out.write(meta)
                with path.open('rb') as inp:
                    while True:
                        if job['cancel'].is_set():raise Cancelled()
                        block=inp.read(CHUNK)
                        if not block:break
                        compressed=zlib.compress(block,level)
                        out.write(b'C');num(out,len(block));num(out,len(compressed))
                        out.write(hashlib.sha256(block).digest());out.write(compressed)
                        job['processed_bytes']+=len(block)
                out.write(b'E');job['processed_files']+=1
            out.write(b'Z');out.flush();os.fsync(out.fileno())
        if job['cancel'].is_set():raise Cancelled()
        os.replace(temp,target);job.update(output=str(target),output_bytes=target.stat().st_size)
    finally:
        if temp.exists():temp.unlink()

def extract(job,source,target,max_files=1000000,max_total=100*1024**3):
    source=Path(source).resolve();dest=Path(target).resolve()
    if not source.is_file():raise ValueError('PVX archive does not exist')
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):raise ValueError('Destination must be empty')
    if dest.is_relative_to(source.parent) and dest==source:raise ValueError('Invalid destination')
    dest.mkdir(parents=True,exist_ok=True)
    job['phase']='extracting';total=0;count=0;seen=set()
    with source.open('rb') as f:
        if exact(f,8)!=MAGIC:raise ValueError('Not a PVX archive')
        version,chunk_size=struct.unpack('>HI',exact(f,6))
        if version!=VERSION or chunk_size!=CHUNK:raise ValueError('Unsupported PVX version')
        while True:
            if job['cancel'].is_set():raise Cancelled()
            tag=exact(f,1)
            if tag==b'Z':
                if f.read(1):raise ValueError('Unexpected trailing data')
                break
            if tag!=b'F':raise ValueError('Invalid PVX record')
            mlen=getnum(f)
            if mlen>65536:raise ValueError('Metadata too large')
            meta=json.loads(exact(f,mlen))
            rel=meta.get('path');size=meta.get('size')
            if not isinstance(rel,str) or not safe_name(rel) or rel in seen or not isinstance(size,int) or isinstance(size,bool) or size<0:raise ValueError('Invalid file metadata')
            seen.add(rel);count+=1;total+=size
            if count>max_files or total>max_total:raise ValueError('Extraction limits exceeded')
            outpath=(dest/rel).resolve()
            if not outpath.is_relative_to(dest):raise ValueError('Unsafe archive path')
            outpath.parent.mkdir(parents=True,exist_ok=True)
            written=0
            with outpath.open('xb') as out:
                while True:
                    if job['cancel'].is_set():raise Cancelled()
                    tag=exact(f,1)
                    if tag==b'E':break
                    if tag!=b'C':raise ValueError('Invalid chunk marker')
                    raw_size=getnum(f);compressed_size=getnum(f)
                    if raw_size==0 or raw_size>CHUNK or compressed_size>CHUNK+65536 or written+raw_size>size:raise ValueError('Invalid chunk sizes')
                    digest=exact(f,32);compressed=exact(f,compressed_size)
                    dec=zlib.decompressobj()
                    try: block=dec.decompress(compressed,raw_size+1)
                    except zlib.error as exc: raise ValueError("Corrupt PVX compressed data") from exc
                    if len(block)!=raw_size or not dec.eof or dec.unused_data or dec.unconsumed_tail or hashlib.sha256(block).digest()!=digest:raise ValueError('Corrupt PVX chunk')
                    out.write(block);written+=raw_size;job['processed_bytes']+=raw_size
            if written!=size:raise ValueError('File length mismatch')
            job['processed_files']+=1
    job.update(output=str(dest),total_files=count,total_bytes=total)
