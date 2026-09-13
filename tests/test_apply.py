from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import apply_to_repo as apply

class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.base=Path(self.tmp.name)
        self.src=self.base/'new';self.dst=self.base/'repo'
        self.src.mkdir();self.dst.mkdir();(self.dst/'.git').mkdir()
        (self.src/'keymap').write_text('new');(self.dst/'keymap').write_text('old')
    def tearDown(self):self.tmp.cleanup()
    def test_backup_and_copy(self):
        w,r=apply.plan(self.src,self.dst); b=apply.install(self.src,self.dst,w,r)
        self.assertEqual((self.dst/'keymap').read_text(),'new')
        self.assertEqual((b/'files/keymap').read_text(),'old')
        self.assertTrue((self.dst/'.git').exists())
    def test_same_path_rejected(self):
        with self.assertRaises(ValueError):apply.plan(self.dst,self.dst)
    def test_nested_source_rejected(self):
        s=self.dst/'unzip';s.mkdir()
        with self.assertRaises(ValueError):apply.plan(s,self.dst)
    def test_missing_git_rejected(self):
        (self.dst/'.git').rmdir()
        with self.assertRaises(ValueError):apply.plan(self.src,self.dst)
    def test_known_legacy_removed_and_backed_up(self):
        p=self.dst/'zephyr/module.yml';p.parent.mkdir();p.write_text('name: zmk-behavior-obrey-combo-boot')
        w,r=apply.plan(self.src,self.dst);b=apply.install(self.src,self.dst,w,r)
        self.assertFalse(p.exists());self.assertTrue((b/'files/zephyr/module.yml').is_file())
    def test_unknown_root_module_rejected(self):
        p=self.dst/'zephyr/module.yml';p.parent.mkdir();p.write_text('name: unrelated-module')
        with self.assertRaises(ValueError):apply.plan(self.src,self.dst)
    def test_symlink_rejected(self):
        (self.dst/'keymap').unlink();(self.dst/'keymap').symlink_to(self.src/'keymap')
        with self.assertRaises(ValueError):apply.plan(self.src,self.dst)
    def test_idempotent(self):
        w,r=apply.plan(self.src,self.dst);apply.install(self.src,self.dst,w,r)
        self.assertEqual(apply.plan(self.src,self.dst),([],[]))
    def test_unrelated_files_untouched(self):
        (self.dst/'mine.txt').write_text('mine')
        w,r=apply.plan(self.src,self.dst);apply.install(self.src,self.dst,w,r)
        self.assertEqual((self.dst/'mine.txt').read_text(),'mine')
    def test_git_files_excluded(self):
        (self.src/'.git').mkdir();(self.src/'.git/config').write_text('never copy')
        w,_=apply.plan(self.src,self.dst);self.assertNotIn('.git/config',w)

if __name__=='__main__':unittest.main()
