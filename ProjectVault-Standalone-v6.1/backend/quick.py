"""Native folder chooser and deterministic output name for one-click PVX."""
from pathlib import Path

def choose_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise RuntimeError('Tkinter is required for native folder selection') from exc
    root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
    try: return filedialog.askdirectory(parent=root,title='PVX化するプロジェクトフォルダを選択',mustexist=True)
    finally: root.destroy()

def quick_options(folder):
    source=Path(folder).resolve()
    if not source.is_dir():raise ValueError('Folder not found')
    base=source.parent / (source.name+'.pvx')
    target=base
    index=2
    while target.exists() or target.with_name(target.name+'.partial').exists():
        target=source.parent / f'{source.name}-{index}.pvx'
        index+=1
    return {'kind':'compress','source':str(source),'target':str(target),'level':6,
            'excludes':['node_modules','.git','__pycache__','*.pyc','.DS_Store']}
