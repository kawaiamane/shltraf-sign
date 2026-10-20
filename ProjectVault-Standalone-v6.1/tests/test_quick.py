import tempfile,unittest
from pathlib import Path
from backend.quick import quick_options
class QuickTests(unittest.TestCase):
 def test_default_output(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'myapp';src.mkdir()
   x=quick_options(src)
   self.assertEqual(Path(x['target']).name,'myapp.pvx')
   self.assertEqual(x['level'],6)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'myapp';src.mkdir();(Path(d)/'myapp.pvx').touch()
   self.assertEqual(Path(quick_options(src)['target']).name,'myapp-2.pvx')
