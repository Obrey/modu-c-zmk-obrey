"""Mutation tests for static preflight. No hardware is mocked as 'verified'."""
from pathlib import Path
import importlib.util
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import check_combo_boot as check
import validate

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'repo'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__','reports'))
        self.keymap=self.root/'config/modu.keymap'
    def tearDown(self): self.tmp.cleanup()
    def mutate(self,old,new):
        text=self.keymap.read_text()
        self.assertIn(old,text)
        self.keymap.write_text(text.replace(old,new,1))
    def reject(self):
        with self.assertRaises((ValueError,SystemExit)):
            check.check(self.root)
    def test_normal(self): self.assertEqual(check.check(self.root)['ordinary_binding_count'],335)
    def test_stock_boot_in_left_combo(self):
        self.mutate('bindings = <&boot135>;','bindings = <&bootloader>;'); self.reject()
    def test_stock_boot_in_right_combo(self):
        self.mutate('bindings = <&boot680>;','bindings = <&bootloader>;'); self.reject()
    def test_two_key_not_three_key(self):
        self.mutate('key-positions = <1 3 5>;','key-positions = <1 5>;'); self.reject()
    def test_changed_observer_window(self):
        self.mutate('window-ms = <80>;','window-ms = <800>;'); self.reject()
    def test_boot_enabled_game(self):
        self.mutate('layers = <L_BASE>;','layers = <L_BASE L_GAME>;'); self.reject()
    def test_no_idle_guard(self):
        self.mutate('require-prior-idle-ms = <300>;','require-prior-idle-ms = <0>;'); self.reject()
    def test_num_order_changed(self):
        self.mutate('&kp N1                  &kp N2','&kp N2                  &kp N1'); self.reject()
    def test_root_module_left_behind(self):
        p=self.root/'zephyr/module.yml'; p.parent.mkdir();p.write_text('name: legacy\n');self.reject()
    def test_legacy_workflow_left_behind(self):
        (self.root/'.github/workflows/obrey-combo-boot-build.yml').write_text('name: Old'); self.reject()
    def test_missing_module(self):
        (self.root/'local-modules/obrey-combo-boot/src/obrey_guard.h').unlink();self.reject()
    def test_module_not_loaded_both_halves(self):
        p=self.root/'build.yaml';p.write_text(p.read_text().replace(';${GITHUB_WORKSPACE}/local-modules/obrey-combo-boot','',1));self.reject()
    def test_property_after_subnode(self):
        text=self.keymap.read_text().replace('        compatible = "zmk,combos";','',1)
        text=text.replace('        /* No combo is active on Game or FnMedia. */',
                          '        compatible = "zmk,combos";\n        /* No combo is active on Game or FnMedia. */',1)
        self.keymap.write_text(text);self.reject()
    def test_game_shift_missing(self):
        self.mutate('&kp LSHFT               &kp Z','&kp A                   &kp Z');self.reject()
    def test_game_arrow_missing(self):
        self.mutate('&kp COMMA               &kp UP','&kp COMMA               &kp PERIOD');self.reject()
    def test_invalid_layer_reference(self):
        self.mutate('&lt L_FN DEL','&lt 9 DEL');self.reject()
    def test_base_extra_none(self):
        self.mutate('&lt L_FN DEL            &trans','&lt L_FN DEL            &none');self.reject()
    def test_module_trigger_missing(self):
        p=self.root/'.github/workflows/build.yml';p.write_text(p.read_text().replace('      - "local-modules/obrey-combo-boot/**"\n','',1));self.reject()
    def test_plain_symbol_edits_other_than_reserved_boot_symbols_allowed(self):
        self.mutate('&kp EQUAL','&kp PLUS');check.check(self.root)
    def test_original_strict_build_pin_check(self):
        p=self.root/'config/west.yml';p.write_text(p.read_text().replace(validate.ZMK_REVISION,'main'))
        original=validate.ROOT;validate.ROOT=self.root
        try:
            with self.assertRaises(SystemExit):validate.check_build_files()
        finally:validate.ROOT=original
    def test_original_driver_path_check(self):
        p=self.root/'build.yaml';p.write_text(p.read_text().replace('zmk-pmw3610-driver','missing-driver'))
        original=validate.ROOT;validate.ROOT=self.root
        try:
            with self.assertRaises(SystemExit):validate.check_build_files()
        finally:validate.ROOT=original
    def test_original_metadata_duplicate_key_check(self):
        p=self.root/'config/modu.json';p.write_text('{"layouts":{},"layouts":{}}')
        original=validate.ROOT;validate.ROOT=self.root
        try:
            with self.assertRaises(SystemExit):validate.check_metadata()
        finally:validate.ROOT=original

if __name__=='__main__':unittest.main()
