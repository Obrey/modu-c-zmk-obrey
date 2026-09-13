#!/usr/bin/env python3
"""Repository preflight. This is NOT a ZMK compile or a physical-device test."""
from __future__ import annotations
import json
import re
from pathlib import Path
import validate as upstream

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def clean(text: str) -> str:
    return upstream._strip_comments(text)


def node(text: str, name: str) -> str:
    text = clean(text)
    match = re.search(rf'(?<![\w-]){re.escape(name)}\s*\{{', text)
    require(match is not None, f'Missing node: {name}')
    opening = text.find('{', match.start())
    return text[opening + 1:upstream._matching_brace(text, opening)]


def prop(body: str, name: str) -> str:
    match = re.search(rf'(?<![\w-]){re.escape(name)}\s*=\s*<(.*?)>\s*;', body, re.S)
    require(match is not None, f'Missing property: {name}')
    return ' '.join(match.group(1).split())


def binding_entries(body: str) -> list[str]:
    raw = prop(body, 'bindings')
    return [' '.join(s.split()) for s in re.findall(r'&[A-Za-z_]\w*[^&]*', raw)]


def numeric_values(value: str, definitions: dict[str, int]) -> list[int]:
    result = []
    for token in value.split():
        if token in definitions:
            result.append(definitions[token])
        else:
            require(bool(re.fullmatch(r'\d+', token)), f'Unresolved numeric token: {token}')
            result.append(int(token))
    return result


def property_order(text: str) -> None:
    """Reject DTS properties placed after a subnode, without pretending to be dtc."""
    text = re.sub(r'^\s*#(?:include|define)\b[^\n]*', '', clean(text), flags=re.M)
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[{};]|[^{};"]+', text)
    child_stack = [False]
    pending = ''
    for token in tokens:
        if token == '{':
            child_stack[-1] = True
            child_stack.append(False)
            pending = ''
        elif token == '}':
            require(len(child_stack) > 1, 'Unexpected closing brace')
            require(not pending.strip(), 'Unterminated declaration before closing brace')
            child_stack.pop()
            pending = ''
        elif token == ';':
            if pending.strip():
                require(not child_stack[-1], 'DTS properties must precede child nodes')
            pending = ''
        else:
            pending += token
    require(len(child_stack) == 1 and not pending.strip(), 'Unbalanced DTS structure')


def check(root: Path = ROOT) -> dict:
    text = (root/'config/modu.keymap').read_text(encoding='utf-8-sig')
    property_order(text)
    layer_nodes = upstream._keymap_layers(text)
    require([n for n, _ in layer_nodes] == ['default_layer','lower_layer','Mouse','game','FnMedia'],
            'Expected only the five agreed layers, with stable names and order')
    require(all(len(v) == 67 for _, v in layer_nodes), 'All layers need 67 bindings')
    definitions = {k:int(v) for k,v in re.findall(r'^\s*#define\s+(L_\w+)\s+(\d+)\s*$',text,re.M)}
    require(definitions == {'L_BASE':0,'L_NAV':1,'L_MOUSE':2,'L_GAME':3,'L_FN':4},
            'Layer definitions do not match layer order')
    layers = {n:binding_entries(node(text,n)) for n,_ in layer_nodes}
    base = layers['default_layer']
    require(tuple(i for i,b in enumerate(base) if b == '&none') == tuple(range(51,57)),
            'Base &none must be exactly 51..56')
    require(base[66] == '&trans', 'Keep Base slot 66 neutral')
    require(base[50] == '&kp RBKT' and base[57] == '&kp GRAVE',
            'Bracket/backtick must remain ordinary keys, not boot holds')
    for n,entries in layers.items():
        require(not any(re.search(r'&(?:bootloader|boot135|boot680|sys_reset)\b',b) for b in entries),
                f'Unexpected direct reset on an ordinary key in {n}')
        for b in entries:
            parts=b.split()
            if parts[0] in ('&mo','&to','&tog','&lt','&sl'):
                require(len(parts)>=2,'Layer behavior missing argument')
                target=numeric_values(parts[1],definitions)[0]
                require(0<=target<len(layers),f'Invalid layer target: {b}')
    for suffix, positions, codes in [('135',[1,3,5],['N1','N3','N5']),
                                     ('680',[6,8,10],['N6','N8','N0'])]:
        combo=node(text,'combo_boot_'+suffix)
        behavior=node(text,'boot'+suffix)
        require(numeric_values(prop(combo,'key-positions'),definitions) == positions,
                'Wrong three-key combo: '+suffix)
        require(prop(combo,'bindings') == '&boot'+suffix,'Combo must call its source-aware behavior')
        require(numeric_values(prop(combo,'layers'),definitions) == [0], 'Boot combos must be Base-only')
        require(prop(combo,'timeout-ms') == '80', 'Keep combo timing at 80 ms')
        require(prop(combo,'require-prior-idle-ms') == '300', 'Keep 300 ms idle guard')
        require(numeric_values(prop(behavior,'key-positions'),definitions) == positions,
                'Observed positions differ from combo positions')
        require(prop(behavior,'window-ms') == '80', 'Observer timing differs from combo timing')
        require(prop(behavior,'bindings') == '&bootloader', 'Only standard source-specific boot action allowed')
        require('compatible = "zmk,behavior-obrey-combo-boot";' in behavior, 'Wrong behavior binding schema')
        require([base[p] for p in positions] == ['&kp '+c for c in codes],
                'Numbers moved: update combo AND observer together')
    for n in ['mouse','enter','back_space','bluetooth_clear']:
        scopes=numeric_values(prop(node(text,n),'layers'),definitions)
        require(3 not in scopes and 4 not in scopes, 'A combo is active in Game or Fn: '+n)
    require(len(re.findall(r'&bootloader\b',clean(text))) == 2, 'Unexpected extra boot action')
    require(not re.search(r'&(?:hm200|hm250|mt|lt|boot\w*)\b',node(text,'game')),
            'Game must not contain hold-tap/reset bindings')
    game=layers['game']
    for p,b in {24:'&kp LCTRL',36:'&kp LSHFT',48:'&kp LEFT_ALT',46:'&kp UP',
                57:'&kp LEFT',58:'&kp DOWN',59:'&kp RIGHT',50:'&mo L_FN'}.items():
        require(game[p]==b, f'Missing agreed game control at position {p}')
    for forbidden in ['maintenance_layer','L_MAINT','boot_hold','safe_boot','safe_reset']:
        require(forbidden not in clean(text),'Old maintenance logic remains: '+forbidden)
    # A root module changes the reusable workflow's base directory and breaks
    # the original absolute hardware paths. Load ONLY our nested module.
    require(not (root/'zephyr/module.yml').exists() and not (root/'zephyr/module.yaml').exists(),
            'Remove a stale root zephyr/module file; the extension is nested now')
    require(not (root/'.github/workflows/obrey-combo-boot-build.yml').exists(),
            'Remove the obsolete experimental @main workflow')
    mod=root/'local-modules/obrey-combo-boot'
    for f in ['zephyr/module.yml','CMakeLists.txt','Kconfig','LICENSE',
              'dts/bindings/behaviors/zmk,behavior-obrey-combo-boot.yaml',
              'src/behavior_combo_boot.c','src/obrey_guard.h']:
        require((mod/f).is_file(),'Missing module file: '+f)
    require('target_sources(app PRIVATE' in (mod/'CMakeLists.txt').read_text(),
            'Observer must be an app source before core combo listener')
    require('dts_root: .' in (mod/'zephyr/module.yml').read_text(),'Missing nested dts root')
    schema=(mod/'dts/bindings/behaviors/zmk,behavior-obrey-combo-boot.yaml').read_text()
    require('include: zero_param.yaml' in schema,'Behavior must take zero runtime parameters')
    build=(root/'build.yaml').read_text()
    require(build.count('${GITHUB_WORKSPACE}/local-modules/obrey-combo-boot')==2,
            'Both build rows must explicitly load the nested module')
    workflow=(root/'.github/workflows/build.yml').read_text()
    for pattern in ['      - "local-modules/obrey-combo-boot/**"','      - "tests/**"']:
        require(workflow.count(pattern)==2,'New source paths need both workflow triggers')
    for cmd in ['python3 scripts/check_combo_boot.py','python3 tests/run_host_tests.py']:
        require(cmd in workflow,'Missing CI preflight: '+cmd)
    layout=json.loads((root/'config/modu.json').read_text())['layouts']['default_transform']['layout']
    require(all(layout[p]['col']<6 for p in [1,3,5]),'135 must be on the left in original metadata')
    require(all(layout[p]['col']>=6 for p in [6,8,10]),'680 must be on the right in original metadata')
    return {'result':'PASS','layers':[n for n,_ in layer_nodes],'ordinary_binding_count':335,
            'boot_135_positions':[1,3,5],'boot_680_positions':[6,8,10],
            'module_layout':'nested, explicitly loaded in both build rows',
            'firmware_build':False,'physical_device_test':False}


if __name__ == '__main__':
    try:
        print(json.dumps(check(),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError) as exc:
        raise SystemExit('ERROR: '+str(exc))
