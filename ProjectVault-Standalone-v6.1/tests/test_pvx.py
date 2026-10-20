import tempfile,unittest,threading,os
from pathlib import Path
from backend import pvx
class TestPVX(unittest.TestCase):
    def job(self):return dict(cancel=threading.Event(),processed_bytes=0,processed_files=0)
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'src';src.mkdir();(src/'sub').mkdir()
            (src/'sub'/'a.txt').write_text('hello'*10000)
            (src/'zero').write_bytes(b'');(src/'data.bin').write_bytes(os.urandom(2500000))
            archive=root/'out.pvx';pvx.compress(self.job(),src,archive,6,[])
            dest=root/'dest';pvx.extract(self.job(),archive,dest)
            for file in src.rglob('*'):
                if file.is_file():self.assertEqual(file.read_bytes(),(dest/file.relative_to(src)).read_bytes())
    def test_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'src';src.mkdir();(src/'a').write_bytes(b'x'*3000)
            archive=root/'out.pvx';pvx.compress(self.job(),src,archive,6,[])
            data=bytearray(archive.read_bytes());data[-3]^=0x01;archive.write_bytes(data)
            with self.assertRaises(ValueError):pvx.extract(self.job(),archive,root/'dest')
    def test_magic(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bad.pvx').write_bytes(b'badbadbad')
            with self.assertRaises(ValueError):pvx.extract(self.job(),root/'bad.pvx',root/'dest')
if __name__=='__main__':unittest.main()
