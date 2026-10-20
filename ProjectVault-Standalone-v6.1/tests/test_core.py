import tempfile,unittest,threading,zipfile
from pathlib import Path
from backend.core import compress,extract,safe_name,scan

def job():return {'cancel':threading.Event(),'phase':'queued','total_files':0,'total_bytes':0,'processed_files':0,'processed_bytes':0}
class TestCore(unittest.TestCase):
 def test_paths(self):
  for x in ('../evil','/absolute','C:/evil','x/../../y'):self.assertFalse(safe_name(x))
  self.assertTrue(safe_name('a/b.txt'))
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);src=p/'source';src.mkdir();(src/'folder').mkdir();(src/'folder'/'日本語.txt').write_text('hello'*500);(src/'node_modules').mkdir();(src/'node_modules'/'skip').write_text('x')
   z=p/'out.zip';compress(job(),src,z,6,['node_modules']);self.assertTrue(z.exists())
   with zipfile.ZipFile(z) as f:self.assertEqual(f.namelist(),['folder/日本語.txt'])
   dst=p/'extracted';extract(job(),z,dst);self.assertEqual((dst/'folder'/'日本語.txt').read_text(),'hello'*500)
 def test_zip_slip(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);z=p/'bad.zip'
   with zipfile.ZipFile(z,'w') as f:f.writestr('../bad.txt','bad')
   with self.assertRaises(ValueError):extract(job(),z,p/'dest')
if __name__=='__main__':unittest.main()
