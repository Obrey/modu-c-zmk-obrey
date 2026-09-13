# Sources and scope

## Files actually read

- User-uploaded `modu-c-zmk-config-main.zip`: original configuration wrapper,
  original validator, workflow, build matrix, JSON layout metadata, packaging
  code and license notices. Exact input ZIP digest is in reports/source-baseline.json.
- The conversation's v3.6 `modu.keymap`: the agreed five-layer personal layout.
  A reference copy is included for comparison.
- The earlier source-aware patch's module: inspected, integrated as a nested
  module and updated to recover observation state after missing release events.

## Public primary technical documentation consulted

- https://zmk.dev/docs/keymaps/behaviors/reset
  Stock combos invoke reset on the central; ordinary reset is source-specific.
- https://zmk.dev/docs/keymaps/combos
  Combo parameters, prior idle and layer scope.
- https://zmk.dev/docs/development/new-behavior
  Binding API, source-specific locality, device/behavior definitions.
- https://zmk.dev/docs/development/events
  External app source listeners run before core listeners; observe and bubble.
- https://zmk.dev/docs/development/module-creation
  Nested module files and devicetree binding registration.
- https://zmk.dev/docs/features/split-keyboards
  The central processes keymaps; the peripheral requires a live link for commands.
- https://github.com/zmkfirmware/zmk/blob/main/.github/workflows/build-user-config.yml
  Current reusable workflow's root-module detection, temporary base-directory
  relocation, and command-line ordering. This moving-branch reference was read
  to identify the former installer's path collision. It is NOT the build pin.

## Exact pins retained from the uploaded original

ZMK and reusable workflow:
`641514a97db345f499dd50b0360e594270f008fe`

MODU-C board, scanner, PMW3610 driver and UF2 tools:
`bee0bb4b812f63f279eb67e928accc89600b5904`

Those external Git source trees could not be retrieved here. No claim is made
that the pinned C sources, schematic, or all headers were re-audited in full.
The ZIP is a complete configuration repository, NOT a self-contained copy of
all west dependencies. Keeping the pins avoids an unrequested firmware upgrade.
The board, shield, trackball configuration and BLE-role assignments were not changed.

## Not completed

Actual pinned ZMK/Zephyr/ARM compilation, GitHub workflow execution, flashing,
physical matrix/trackball operation, BLE reset dispatch and Keymap Editor round-trip.
The observed source logic is tested against mocks, not the actual transport stack.
No UF2 is included and no firmware binary is claimed to have been built.
