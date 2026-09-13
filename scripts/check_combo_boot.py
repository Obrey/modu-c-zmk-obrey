#!/usr/bin/env python3
"""Check the direct-boot extension, not the user's chosen typing/game layout.

Ordinary combo names, ordinary combo presence, and ordinary key placements are
not an API. Keymap Editor may rename/delete them. Discover actual nodes instead.
The original scripts/validate.py still checks the hardware/packaging contract.
This preflight is not a compiler and does not certify firmware or hardware.
"""
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



def child_nodes(body: str) -> list[tuple[str, list[str], str]]:
    """Read immediate DTS children, retaining labels used by &references.

    This covers the literal DTS emitted by this config/Keymap Editor. It is not
    a C preprocessor; unknown expressions fail rather than being guessed.
    """
    body = clean(body)
    # Keep offsets while hiding string literals from the node-name scanner.
    masked = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: ' ' * len(m.group()), body)
    pattern = re.compile(
        r'(?<![\w-])(?P<labels>(?:[A-Za-z_]\w*\s*:\s*)*)'
        r'(?P<name>[A-Za-z_][\w,@-]*)\s*\{'
    )
    result = []
    position = 0
    while (match := pattern.search(masked, position)) is not None:
        opening = masked.find('{', match.start())
        closing = upstream._matching_brace(masked, opening)
        labels = re.findall(r'([A-Za-z_]\w*)\s*:', match.group('labels'))
        result.append((match.group('name'), labels, body[opening + 1:closing]))
        position = closing + 1
    return result


def is_compatible(body: str, compatible: str) -> bool:
    return re.search(r'\bcompatible\s*=\s*"' + re.escape(compatible) + r'"\s*;', body) is not None


def check(root: Path = ROOT) -> dict:
    text = (root/'config/modu.keymap').read_text(encoding='utf-8-sig')
    property_order(text)
    definitions = {k: int(v, 0) for k, v in re.findall(
        r'^\s*#define\s+([A-Za-z_]\w*)\s+(0[xX][0-9a-fA-F]+|[0-9]+)\s*$', clean(text), re.M
    )}
    layer_nodes = upstream._keymap_layers(text)
    require(len(layer_nodes) >= 2, 'Expected at least two keymap layers')
    require(all(len(v) == 67 for _, v in layer_nodes), 'All layers need 67 bindings')
    # Scope lookup to keymap, not combos/behaviors with possibly identical names.
    keymap = node(text, 'keymap')
    layers = {n: binding_entries(node(keymap, n)) for n, _ in layer_nodes}
    require(len(layers) == len(layer_nodes), 'Duplicate layer node names')
    base = layers[layer_nodes[0][0]]
    require(tuple(i for i, b in enumerate(base) if b == '&none') == tuple(range(51,57)),
            'Base &none must be exactly 51..56')
    # Do not demand particular names/locations for mouse, arrows or punctuation.
    for name, entries in layers.items():
        for binding in entries:
            parts = binding.split()
            if parts[0] in ('&mo', '&to', '&tog', '&lt', '&sl'):
                require(len(parts) >= 2, 'Layer behavior missing argument in ' + name)
                target = numeric_values(parts[1], definitions)[0]
                require(0 <= target < len(layers), 'Invalid layer target: ' + binding)

    behavior_nodes = child_nodes(node(text, 'behaviors'))
    boot_behaviors = {}
    for name, labels, body in behavior_nodes:
        if is_compatible(body, 'zmk,behavior-obrey-combo-boot'):
            require(bool(labels), 'Source-aware boot behavior needs a DTS label: ' + name)
            for label in labels:
                require(label not in boot_behaviors, 'Duplicate boot behavior label: ' + label)
                boot_behaviors[label] = (name, body)
    require(bool(boot_behaviors), 'No source-aware boot behaviors found')

    combos = child_nodes(node(text, 'combos'))
    require(bool(combos), 'No combo definitions found')
    # All ordinary combos may be renamed/deleted/edited; check real coordinates.
    for name, _, body in combos:
        positions = numeric_values(prop(body, 'key-positions'), definitions)
        require(len(positions) >= 2 and len(set(positions)) == len(positions),
                'Combo needs at least two distinct positions: ' + name)
        require(all(0 <= p < 67 for p in positions), 'Combo position out of range: ' + name)
        if re.search(r'\blayers\s*=', body):
            scope = numeric_values(prop(body, 'layers'), definitions)
            require(scope and all(0 <= n < len(layers) for n in scope),
                    'Combo layer out of range: ' + name)

    selected_names = []
    for suffix, positions, codes in [('135', [1,3,5], ['N1','N3','N5']),
                                     ('680', [6,8,10], ['N6','N8','N0'])]:
        matches = [(name, body) for name, _, body in combos
                   if sorted(numeric_values(prop(body, 'key-positions'), definitions)) == positions]
        require(len(matches) == 1,
                f'Expected one direct {suffix} boot combo at positions {positions}; found {len(matches)}')
        name, combo = matches[0]
        selected_names.append(name)
        target = prop(combo, 'bindings')
        require(re.fullmatch(r'&[A-Za-z_]\w*', target) is not None,
                'Boot combo must invoke one zero-parameter source-aware behavior: ' + name)
        label = target[1:]
        require(label in boot_behaviors,
                f'{suffix} must call the source-aware boot behavior, not stock &bootloader')
        _, behavior = boot_behaviors[label]
        require(numeric_values(prop(combo, 'layers'), definitions) == [0],
                'Boot combos must be Base-only: ' + name)
        require(numeric_values(prop(combo, 'timeout-ms'), definitions) == [80],
                'Keep boot combo timing at 80 ms: ' + name)
        require(numeric_values(prop(combo, 'require-prior-idle-ms'), definitions) == [300],
                'Keep 300 ms boot idle guard: ' + name)
        require(sorted(numeric_values(prop(behavior, 'key-positions'), definitions)) == positions,
                'Observed positions differ from combo positions: ' + name)
        require(numeric_values(prop(behavior, 'window-ms'), definitions) == [80],
                'Observer timing differs from combo timing: ' + name)
        require(prop(behavior, 'bindings') == '&bootloader',
                'Source-aware action must be standard &bootloader: ' + label)
        require([base[p] for p in positions] == ['&kp ' + code for code in codes],
                'Numbers moved: update combo AND source observer together: ' + suffix)
    for name, _, combo in combos:
        if name not in selected_names:
            require(not any('&' + label == prop(combo, 'bindings') for label in boot_behaviors),
                    'Unexpected extra combo calling a source-aware boot action: ' + name)
    for name, entries in layers.items():
        require(not any(binding.split()[0][1:] in boot_behaviors for binding in entries),
                'Source-aware boot actions belong on the two combos, not ordinary keys: ' + name)
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
    return {'result': 'PASS', 'layers': [n for n, _ in layer_nodes],
            'ordinary_binding_count': sum(len(v) for v in layers.values()),
            'boot_135_positions': [1,3,5], 'boot_680_positions': [6,8,10],
            'checked_boot_combo_nodes': selected_names,
            'ordinary_combo_names_or_presence_fixed': False,
            'ordinary_typing_and_game_key_placements_fixed': False,
            'module_layout': 'nested, explicitly loaded in both build rows',
            'firmware_build': False, 'physical_device_test': False}


if __name__ == '__main__':
    try:
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit('ERROR: ' + str(exc))
