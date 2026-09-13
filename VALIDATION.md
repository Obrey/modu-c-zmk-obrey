# Rebuild verification — 2026-09-13

This report applies to the uploaded-original-based Obrey rebuild, not an
uninspected live GitHub branch. The original historical report is preserved
as `reference/UPSTREAM_VALIDATION.md`.

## Actually executed in this environment

1. The uploaded original repository's unmodified `scripts/validate.py` and
   `scripts/selftest.py`, before modification: PASS.
2. The original unmodified metadata and keymap validation functions, applied
   to the rebuilt repository: PASS.
3. Rebuilt `scripts/validate.py`: PASS. Its sole logic change is adding the
   explicit nested behavior-module path to the exact expected CMake argument.
   All original pins, target order, placeholder rules, license checks,
   workflow/package checks and quoted-list checks remain enforced.
4. Rebuilt `scripts/selftest.py` (unchanged): PASS for HEX/UF2 synthetic fixtures.
   These fixtures are NOT compiled MODU firmware.
5. `scripts/check_combo_boot.py`: PASS. Five 67-entry layers, matching three-key
   combo/observer positions, Base-only scope, ordinary symbol restoration,
   nested-module wiring, and devicetree property-before-child order.
6. 32 Python tests: PASS (22 repository checks/mutations; 10 safe-copy tests).
7. Actual C observer/dispatcher source compiled on the host against mocked
   ZMK/Zephyr APIs and transport: 25 scenarios PASS, repeated with behavior
   metadata both disabled and enabled. The compiler uses -Wall -Wextra -Werror.
8. Every ordinary layer binding compared with the agreed v3.6: all 335 unchanged.
9. YAML syntax, Python syntax, Bash syntax for workflow shell blocks, archive
   CRC/path/duplicate checks, and extracted-byte comparison: PASS.

## Improvements over the earlier generic patch

- No root `zephyr/module.yml`: avoid the reusable workflow moving the west
  workspace while hardware CMake paths still reference GITHUB_WORKSPACE.
- Use `local-modules/`, not west's cached `modules/` dependency directory,
  so dependency-cache restoration cannot replace the custom source files.
- A single explicit ZMK_EXTRA_MODULES argument contains the two original modules
  plus `local-modules/obrey-combo-boot` for each half. No duplicate -D flag overwrite.
- Keep one original pinned workflow, with all original UF2 conversion/validation
  and notices. No separate moving-branch workflow bypassing packaging.
- Properties precede child nodes in the keymap; the earlier preview's misplaced
  combo `compatible` property is not carried forward.
- Source observer re-arms safely after a remote boot prevented key-up packets;
  stale replays and incomplete replacement chords still cannot reset a device.
- Unknown/mixed/stale input or dispatch failures never silently reset the central.
- Existing scripts are retained and extended, not disabled to get past an error.
- Backup copier detects known incompatible legacy patch files and removes only
  recognized generated files after backing them up. Git history/remotes unchanged.

## Explicitly not executed

- Fetching the pinned ZMK/Zephyr/hardware dependency trees.
- Actual ARM firmware compilation or linking; no UF2 build output was produced.
- GitHub Actions, physical flashing, source-specific reset over real BLE,
  scanning, trackballs, power states, or Keymap Editor round-trip.
- Windows execution of INSTALL.cmd; its Python copier was tested on the host.

The configuration ZIP is suitable for the next integration-build step, but
is not a hardware-certified firmware release. Do not treat host mock tests as
proof that the real remote half has received a command. Retain a known-good
firmware and a physical reset method when first testing.
