"""Mutation tests for static preflight. No hardware is mocked as 'verified'."""
from pathlib import Path
import importlib.util
import shutil
import sys
import tempfile
import unittest
import re

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import check_combo_boot as check
import validate

# These mutation tests need a fixed fixture, NOT the user's live keymap.
# The preceding CI step runs check() on the user's real configuration.
# The fixture is the originally distributed layout; it is never installed.
REFERENCE_KEYMAP = r'''
/*
 * Obrey MODU-C rebuild 4.0 -- based on the uploaded original config ZIP.
 * Original MODU material: Copyright (c) 2026 EKS Inc.; created by Ryu.
 * SPDX-License-Identifier: LicenseRef-EKS-NonCommercial-1.0
 * Unofficial non-commercial modification; preserve LICENSE and NOTICE.md.
 *
 * Base=0, Nav=1, Mouse=2, Game=3, FnMedia=4. No maintenance layer.
 * Base: 1+3+5 -> boot the source of those keys; 6+8+0 -> their source.
 * True three-key combos: 80 ms window, 300 ms prior input idle, no long hold.
 * REQUIRES modules/obrey-combo-boot; this is not a standalone keymap file.
 * All 335 ordinary bindings are retained from the agreed v3.6 keymap.
 * Base placeholders 51..56; slot 66 is neutral, not assumed nonexistent.
 * Board/trackball source revisions and metadata are retained from the ZIP.
 * Firmware build and physical tests are separate from source/host tests.
 */

#define L_BASE  0
#define L_NAV   1
#define L_MOUSE 2
#define L_GAME  3
#define L_FN    4

#define ZMK_POINTING_DEFAULT_MOVE_VAL 1200
#define ZMK_POINTING_DEFAULT_SCRL_VAL 25

#include <input/processors.dtsi>
#include <zephyr/dt-bindings/input/input-event-codes.h>
#include <behaviors.dtsi>
#include <dt-bindings/zmk/bt.h>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/outputs.h>
#include <dt-bindings/zmk/pointing.h>

/* Only keyboard-generated mouse motion/scroll. Not the physical trackball. */
&mmv_input_listener {
    input-processors = <&zip_xy_scaler 2 1>;
};
&msc_input_listener {
    input-processors = <&zip_scroll_scaler 2 1>;
};
&msc {
    acceleration-exponent = <1>;
    time-to-max-speed-ms = <100>;
    delay-ms = <0>;
};
&mmv {
    time-to-max-speed-ms = <500>;
    acceleration-exponent = <1>;
    trigger-period-ms = <16>;
};

/ {
    behaviors {
        // Real combo-source dispatch. Standard &bootloader alone loses the side.
        boot135: boot135 {
            compatible = "zmk,behavior-obrey-combo-boot";
            #binding-cells = <0>;
            display-name = "Boot left: 1+3+5";
            key-positions = <1 3 5>;
            window-ms = <80>;
            bindings = <&bootloader>;
        };
        boot680: boot680 {
            compatible = "zmk,behavior-obrey-combo-boot";
            #binding-cells = <0>;
            display-name = "Boot right: 6+8+0";
            key-positions = <6 8 10>;
            window-ms = <80>;
            bindings = <&bootloader>;
        };

        hm200: hm200 {
            compatible = "zmk,behavior-hold-tap";
            label = "HOMEROW_MODS";
            bindings = <&kp>, <&kp>;
            #binding-cells = <2>;
            tapping-term-ms = <200>;
            quick-tap-ms = <130>;
            require-prior-idle-ms = <(-1)>;
            flavor = "tap-preferred";
        };

        hm250: hm250 {
            compatible = "zmk,behavior-hold-tap";
            label = "HM250";
            bindings = <&kp>, <&kp>;
            #binding-cells = <2>;
            tapping-term-ms = <250>;
            quick-tap-ms = <130>;
            require-prior-idle-ms = <(-1)>;
            flavor = "tap-preferred";
        };
    };

    combos {
        compatible = "zmk,combos";

        // Direct three-key combos. The custom behavior restores the actual side.
        combo_boot_135 {
            timeout-ms = <80>;
            require-prior-idle-ms = <300>;
            key-positions = <1 3 5>;
            bindings = <&boot135>;
            layers = <L_BASE>;
        };
        combo_boot_680 {
            timeout-ms = <80>;
            require-prior-idle-ms = <300>;
            key-positions = <6 8 10>;
            bindings = <&boot680>;
            layers = <L_BASE>;
        };

        /* No combo is active on Game or FnMedia. */
        mouse {
            timeout-ms = <50>;
            key-positions = <41 62>;
            bindings = <&tog L_MOUSE>;
            layers = <L_BASE L_NAV L_MOUSE>;
        };
        enter {
            timeout-ms = <50>;
            key-positions = <33 32>;
            bindings = <&kp ENTER>;
            layers = <L_BASE>;
        };
        back_space {
            timeout-ms = <50>;
            key-positions = <31 32>;
            bindings = <&kp BACKSPACE>;
            layers = <L_BASE>;
        };

        /* Intentional pairing-clear gesture: Nav held, then the 1 and 0 number keys together.
         * Not active on Game or FnMedia. Clears only the selected Bluetooth profile.
         */
        bluetooth_clear {
            timeout-ms = <50>;
            require-prior-idle-ms = <300>;
            key-positions = <1 10>;
            bindings = <&bt BT_CLR>;
            layers = <L_NAV>;
        };
    };

    keymap {
        compatible = "zmk,keymap";
        // Base letters/home-row mods kept; new keys restore missing punctuation. 0 enters Game.
        default_layer {
            display-name = "Base";
            bindings = <
                /* 00..11 */ &to L_GAME              &kp N1                  &kp N2                  &kp N3                  &kp N4                  &kp N5                  &kp N6                  &kp N7                  &kp N8                  &kp N9                  &kp N0                  &kp MINUS
                /* 12..23 */ &mt LG(A) LG(Z)         &kp SLASH               &kp W                   &kp E                   &kp R                   &kp T                   &kp Y                   &kp U                   &kp I                   &kp O                   &kp SEMICOLON           &kp EQUAL
                /* 24..35 */ &mt LG(X) LG(C)         &hm250 LCTRL A          &hm200 LALT S           &hm200 LEFT_GUI D       &hm200 LSHFT F          &kp G                   &kp H                   &hm200 LSHFT J          &hm200 LEFT_GUI K       &hm200 LALT L           &hm250 LCTRL P          &kp APOS
                /* 36..47 */ &kp LG(V)               &kp Z                   &kp X                   &kp C                   &kp V                   &kp Q                   &kp N                   &kp M                   &kp B                   &kp COMMA               &kp PERIOD              &kp BSLH
                /* 48..59 */ &kp TAB                 &kp LBKT                &kp RBKT                &none                   &none                   &none                   &none                   &none                   &none                   &kp GRAVE               &mkp LCLK               &mkp RCLK
                /* 60..66 */ &kp ESC                 &kp SPACE               &lt L_NAV CAPSLOCK      &kp ENTER               &kp BACKSPACE           &lt L_FN DEL            &trans
            >;
        };

        // Nav; node name lower_layer retained for compatibility with existing repo checks.
        lower_layer {
            display-name = "Nav";
            bindings = <
                /* 00..11 */ &to L_BASE              &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans
                /* 12..23 */ &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &kp UP                  &trans                  &trans                  &trans
                /* 24..35 */ &trans                  &trans                  &kp LG(LC(LS(N4)))      &kp LG(LS(N5))          &trans                  &trans                  &kp TAB                 &kp LEFT                &kp DOWN                &kp RIGHT               &kp HOME                &trans
                /* 36..47 */ &trans                  &trans                  &trans                  &trans                  &kp LG(LC(LS(N3)))      &trans                  &kp INS                 &kp PG_UP               &kp PG_DN               &kp END                 &kp RALT                &trans
                /* 48..59 */ &trans                  &trans                  &trans                  &none                   &none                   &none                   &none                   &none                   &none                   &trans                  &trans                  &trans
                /* 60..66 */ &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &none
            >;
        };

        // Mouse mode; 0 or left Escape returns to Base. 50 temporarily activates FnMedia.
        Mouse {
            display-name = "Mouse";
            bindings = <
                /* 00..11 */ &to L_BASE              &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans                  &trans
                /* 12..23 */ &trans                  &kp LG(MINUS)           &kp LG(EQUAL)           &none                   &kp LG(RBKT)            &kp LG(LBKT)            &kp LG(LBKT)            &kp LG(RBKT)            &mmv MOVE_UP            &kp LG(EQUAL)           &kp LG(MINUS)           &trans
                /* 24..35 */ &trans                  &none                   &mkp MCLK               &mkp RCLK               &mkp LCLK               &none                   &kp LG(LBKT)            &mmv MOVE_LEFT          &mmv MOVE_DOWN          &mmv MOVE_RIGHT         &trans                  &trans
                /* 36..47 */ &trans                  &msc SCRL_RIGHT         &msc SCRL_LEFT          &msc SCRL_UP            &msc SCRL_DOWN          &trans                  &kp LG(RBKT)            &msc SCRL_UP            &msc SCRL_DOWN          &msc SCRL_LEFT          &msc SCRL_RIGHT         &trans
                /* 48..59 */ &kp TAB                 &none                   &mo L_FN                &none                   &none                   &none                   &none                   &none                   &none                   &mkp MCLK               &mkp LCLK               &mkp RCLK
                /* 60..66 */ &to L_BASE              &trans                  &trans                  &mkp RCLK               &mkp LCLK               &mkp MCLK               &none
            >;
        };

        // Gaming: plain key/button presses; 0 returns to Base. Dot moved from 46 to 35.
        game {
            display-name = "Game";
            bindings = <
                /* 00..11 */ &to L_BASE              &kp N1                  &kp N2                  &kp N3                  &kp N4                  &kp N5                  &kp N6                  &kp N7                  &kp N8                  &kp N9                  &kp N0                  &kp MINUS
                /* 12..23 */ &kp TAB                 &kp SLASH               &kp W                   &kp E                   &kp R                   &kp T                   &kp Y                   &kp U                   &kp I                   &kp O                   &kp SEMICOLON           &kp EQUAL
                /* 24..35 */ &kp LCTRL               &kp A                   &kp S                   &kp D                   &kp F                   &kp G                   &kp H                   &kp J                   &kp K                   &kp L                   &kp P                   &kp PERIOD
                /* 36..47 */ &kp LSHFT               &kp Z                   &kp X                   &kp C                   &kp V                   &kp Q                   &kp N                   &kp M                   &kp B                   &kp COMMA               &kp UP                  &kp BSLH
                /* 48..59 */ &kp LEFT_ALT            &mkp RCLK               &mo L_FN                &none                   &none                   &none                   &none                   &none                   &none                   &kp LEFT                &kp DOWN                &kp RIGHT
                /* 60..66 */ &kp ESC                 &kp SPACE               &mkp LCLK               &kp ENTER               &kp BACKSPACE           &kp DELETE              &none
            >;
        };

        // Fn overlay above Game.
        FnMedia {
            display-name = "FnMedia";
            bindings = <
                /* 00..11 */ &kp F11                    &kp F1                     &kp F2                     &kp F3                     &kp F4                     &kp F5                     &kp F6                     &kp F7                     &kp F8                     &kp F9                     &kp F10                    &kp F12
                /* 12..23 */ &trans                     &kp GRAVE                  &kp PSCRN                  &kp SLCK          &kp C_PAUSE      &kp CAPSLOCK               &bt BT_SEL 0               &bt BT_SEL 1               &bt BT_SEL 2               &bt BT_SEL 3               &bt BT_SEL 4               &kp K_APP
                /* 24..35 */ &trans                     &trans                     &trans                     &trans                     &trans                     &trans                     &kp C_PREV                 &kp C_PP                   &kp C_NEXT                 &kp C_VOL_DN               &kp C_VOL_UP               &kp C_MUTE
                /* 36..47 */ &trans                     &kp LBKT                   &kp RBKT                   &mkp MCLK                  &msc SCRL_UP               &msc SCRL_DOWN             &out OUT_USB               &out OUT_BLE               &out OUT_TOG               &kp APOS                   &trans                     &to L_MOUSE
                /* 48..59 */ &trans                     &trans                     &trans                     &none                      &none                      &none                      &none                      &none                      &none                      &trans                     &trans                     &trans
                /* 60..66 */ &trans                     &trans                     &trans                     &trans                     &trans                     &trans                     &none
            >;
        };

    };
};
'''

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'repo'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__','reports'))
        self.keymap=self.root/'config/modu.keymap'
        self.keymap.write_text(REFERENCE_KEYMAP, encoding='utf-8')
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
    def test_game_modifier_edit_allowed(self):
        self.mutate('&kp LSHFT               &kp Z','&kp A                   &kp Z');check.check(self.root)
    def test_game_arrow_edit_allowed(self):
        self.mutate('&kp COMMA               &kp UP','&kp COMMA               &kp PERIOD');check.check(self.root)
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

    def test_mouse_combo_renamed(self):
        self.mutate('        mouse {', '        mouse_toggle {')
        check.check(self.root)
    def test_mouse_combo_deleted(self):
        text, count = re.subn(r'        mouse \{.*?\n        \};\n', '', self.keymap.read_text(), count=1, flags=re.S)
        self.assertEqual(count, 1)
        self.keymap.write_text(text)
        check.check(self.root)
    def test_all_ordinary_combos_renamed(self):
        for old, new in [('mouse', 'pointer_mode'), ('enter', 'enter_combo'),
                         ('back_space', 'backspace_combo'), ('bluetooth_clear', 'clear_pairing')]:
            self.mutate('        ' + old + ' {', '        ' + new + ' {')
        check.check(self.root)
    def test_all_ordinary_combos_deleted(self):
        text = self.keymap.read_text()
        for name in ['mouse', 'enter', 'back_space', 'bluetooth_clear']:
            text, count = re.subn(r'        ' + name + r' \{.*?\n        \};\n', '', text, count=1, flags=re.S)
            self.assertEqual(count, 1)
        self.keymap.write_text(text)
        check.check(self.root)
    def test_boot_combo_nodes_renamed(self):
        self.mutate('combo_boot_135 {', 'my_left_boot {')
        self.mutate('combo_boot_680 {', 'my_right_boot {')
        check.check(self.root)
    def test_behavior_labels_and_node_names_differ(self):
        text = self.keymap.read_text()
        text = text.replace('boot135: boot135 {', 'left_reset_action: behavior_left {')
        text = text.replace('&boot135', '&left_reset_action')
        text = text.replace('boot680: boot680 {', 'right_reset_action: behavior_right {')
        text = text.replace('&boot680', '&right_reset_action')
        self.keymap.write_text(text)
        check.check(self.root)
    def test_layer_node_names_not_forced(self):
        self.mutate('        Mouse {', '        pointer_layer {')
        self.mutate('        game {', '        gaming_layer {')
        self.mutate('        FnMedia {', '        function_layer {')
        check.check(self.root)
    def test_numeric_layer_references_allowed(self):
        text = self.keymap.read_text()
        for symbol, value in [('L_BASE',0),('L_NAV',1),('L_MOUSE',2),('L_GAME',3),('L_FN',4)]:
            text = re.sub(r'^#define\s+' + symbol + r'\s+\d+\s*$', '', text, flags=re.M)
            text = re.sub(r'\b' + symbol + r'\b', str(value), text)
        self.keymap.write_text(text)
        check.check(self.root)
    def test_bracket_and_backtick_can_be_edited(self):
        self.mutate('&kp RBKT', '&kp BSLH')
        self.mutate('&kp GRAVE', '&kp APOS')
        check.check(self.root)
    def test_missing_boot_combo_still_rejected(self):
        text, count = re.subn(r'        combo_boot_680 \{.*?\n        \};\n', '', self.keymap.read_text(), count=1, flags=re.S)
        self.assertEqual(count, 1)
        self.keymap.write_text(text)
        self.reject()
    def test_boot_wrong_observed_side_rejected(self):
        self.mutate('key-positions = <6 8 10>;', 'key-positions = <1 3 5>;')
        self.reject()
    def test_duplicate_boot_combo_rejected(self):
        text = self.keymap.read_text()
        match = re.search(r'        combo_boot_135 \{.*?\n        \};', text, re.S)
        self.assertIsNotNone(match)
        duplicate = match.group().replace('combo_boot_135', 'extra_duplicate')
        self.keymap.write_text(text.replace(match.group(), match.group() + '\n' + duplicate))
        self.reject()
    def test_invalid_ordinary_combo_scope_rejected(self):
        self.mutate('layers = <L_BASE L_NAV L_MOUSE>;', 'layers = <L_BASE 99>;')
        self.reject()
    def test_invalid_ordinary_combo_position_rejected(self):
        self.mutate('key-positions = <41 62>;', 'key-positions = <41 99>;')
        self.reject()
    def test_core_missing_source_behavior_rejected(self):
        self.mutate('compatible = "zmk,behavior-obrey-combo-boot";', 'compatible = "zmk,behavior-key-press";')
        self.reject()
    def test_reordered_chord_position_list_allowed(self):
        text = self.keymap.read_text().replace('<1 3 5>', '<5 1 3>')
        self.keymap.write_text(text)
        check.check(self.root)

if __name__=='__main__':unittest.main()
