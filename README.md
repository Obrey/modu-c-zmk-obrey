# Obrey MODU-C — 원본 ZIP 기반 재구성본 4.0

`22sh22/modu-c-zmk-config`에서 내려받아 이 대화에 첨부한
`modu-c-zmk-config-main.zip`을 기반으로 구성했습니다.
이전 설치 패치를 먼저 적용할 필요가 없는 **설정 저장소 전체**입니다.
원본의 EKS 비상업 라이선스·저작자 표시를 유지한 비공식 개인 수정본입니다.

**키맵만 따로 복사하지 마세요. `local-modules/`와 `build.yaml`이 함께 필요합니다.**
UF2 완성 파일은 포함하지 않습니다. 실제 펌웨어는 Actions에서 빌드해야 합니다.

## 변경 범위

원본의 `config/west.yml`, 보드 이름, 좌우 shield, 하드웨어 소스 고정 revision,
트랙볼 드라이버 경로, `config/modu.json`과 `config/info.json`은 그대로입니다.
원본의 HEX 정규화, UF2 검증·패키징, 라이선스 포함 기능도 유지했습니다.

사용자가 이 대화에서 확정한 v3.6의 일반 키 배치 335개(5×67)를 모두 유지하고,
부트로더 콤보의 실행 대상 처리만 확장했습니다. 따라서 원본 ZIP의 예제
3레이어 배열로 되돌린 것은 아닙니다.

| 번호 | 레이어 | 역할 |
|---:|---|---|
| 0 | Base | 평상시 문자·숫자·기호, 기존 왼쪽 단축키열과 홈로우 모드 |
| 1 | Nav | 기존 이동·편집 |
| 2 | Mouse | 기존 클릭·스크롤·키보드식 포인터 이동 |
| 3 | Game | 일반 문자키, 독립 Ctrl/Shift/Alt, 방향키와 클릭 |
| 4 | FnMedia | F키·미디어·연결 설정 |

**Maintenance 레이어, 부트로더용 Fn/Nav 추가 조작, 백틱/대괄호 3초 홀드,
클릭키에 얹는 부트로더 기능은 없습니다.**

## 부트로더: 세 키를 함께 누르기

평상시 **Base**에서 모든 키를 놓고 약 반초 쉰 다음 아래 세 키를 함께 누릅니다.

| 조합 | 의도한 대상 |
|---|---|
| `1 + 3 + 5` | 왼쪽 반쪽 |
| `6 + 8 + 0` | 오른쪽 반쪽 |

긴 홀드나 추가 실행키는 없습니다. 세 키의 눌림이 80ms 이내에 들어오고,
세 키 모두 눌린 상태가 되어야 합니다. `135` 또는 `680`을 한 글자씩
눌렀다 떼며 입력하는 것과 다릅니다. 직전 일반 입력 이후 300ms 보호를 유지합니다.
Base 숫자 1·3·5·6·8·0은 콤보 판정 때문에 조건에 따라 최대 80ms 대기가
추가될 수 있습니다. 새 콤보는 Game/Nav/Mouse/FnMedia에서는 비활성입니다.

숫자 **0은 10번 위치**, 게임 전환키는 **0번 위치**입니다. 둘을 혼동하지 마세요.

### 좌우를 구분하는 방식

기본 ZMK 콤보가 호출하는 `&bootloader`는 중앙 장치를 대상으로 합니다.
여기서는 콤보가 `&boot135` / `&boot680`이라는 작은 사용자 정의 동작을 호출합니다.
이 동작은 같은 세 키의 실제 입력 출처를 먼저 관찰하고, 표준 부트로더 명령에
그 출처를 붙여 전달합니다. 중앙=왼쪽, 주변장치=0번처럼 고정하지 않습니다.
관찰 실패·혼합 출처·오래된 입력·Base 이외의 실행은 거부합니다.
전송 실패 시 다른 반쪽을 대신 재부팅하는 fallback은 없습니다.

이 방식은 별도 레이어가 아니며, ZMK core나 무선 전송 프로토콜을 패치하지 않습니다.
실제 좌우 전송·부트로더 작동은 기기에서 아직 시험하지 않았습니다.

### 업데이트 순서

업데이트할 반쪽을 **USB 데이터 케이블**로 PC에 연결한 상태에서 실행합니다.
양쪽이 정상 실행·연결되어 있어야 반대쪽으로 소프트웨어 명령을 전달할 수 있습니다.
**한쪽 진입 → 해당 UF2 설치 → 정상 재시작·재연결 확인 → 다른 쪽** 순서입니다.
두 쪽을 동시에 부트로더로 보내려 하지 마세요. 입력 처리를 맡은 쪽이 먼저
멈추면 다른 쪽의 콤보를 처리할 수 없습니다.

새 콤보는 이 펌웨어를 처음 설치한 뒤부터 쓸 수 있습니다.
최초 설치, 연결 손상, 펌웨어 오류 때에는 물리 리셋 방법이 여전히 필요합니다.
부트로더 진입은 공장 초기화/블루투스 페어링 삭제가 아닙니다.

## 게임 배열: 기존 합의안 유지

문자 Q/B/P 등의 커스텀 위치를 포함해 기존 Base 문자 위치를 유지하며,
Game에서는 홈로우 모드와 탭/홀드 겸용키를 제거했습니다.
Game의 방향키는 원본 에디터 메타데이터에서 아래처럼 모입니다.

```text
                  ↑ (46)
           ← (57) ↓ (58) → (59)
```

Game에서 마침표는 오른쪽 홈로우 맨 끝 35번입니다. Base의 마침표는 46번 그대로입니다.
왼쪽 바깥 24/36은 Ctrl/Shift, 보조행 48은 Alt, 49는 우클릭, 50은 Fn입니다.
왼엄지는 Esc/Space/좌클릭, 오른엄지는 Enter/Backspace/Delete입니다.
Game Fn(50)을 누른 채 숫자 1~0은 F1~F10, 최상단 양끝은 F11/F12입니다.
FnMedia가 Game 위에 있어 F키가 Game 문자키에 가려지지 않습니다.
키보드 전체 무선 지연이 0이라는 뜻은 아닙니다.

## 설치: Windows 기존 저장소로 적용

### 권장: 백업하는 복사 도구

1. ZIP을 **기존 Git 저장소 밖의 새 폴더**에 풉니다.
2. `INSTALL.cmd`를 실행합니다. Python 3가 필요합니다.
3. 대상 경로를 확인합니다. 기본값은 `D:\Dev\projects\modu-c-zmk-obrey`입니다.
4. 변경 목록을 검토한 뒤 `y`를 입력합니다. 덮어쓸 파일과 제거할 구버전 파일은
   저장소 **옆의 날짜별 백업 폴더**에 저장됩니다. `.git`과 Git remote는 건드리지 않습니다.
5. 원래 저장소에서 `git status --short`, `git diff`로 검토하고,
   도구가 출력한 파일별 `git add` 명령 → `git commit` → `git push`를 실행합니다.
6. GitHub Actions의 **Build MODU-C ZMK firmware** 결과를 확인합니다.
   모두 성공한 실행의 **modu-c-firmware** 아티팩트에서 좌우 UF2를 받습니다.

도구는 자동으로 커밋·푸시하지 않습니다. 이후 직접 편집한 키맵도 백업하지만,
이 재구성본으로 교체하므로 대화 이후의 개인 수정은 비교해서 다시 반영해야 합니다.
`STOP`이 표시되면 그대로 중단하고 출력 내용을 확인하세요.

명령어로 변경 예정 목록만 보기:

```powershell
py -3 scripts\apply_to_repo.py --target "D:\Dev\projects\modu-c-zmk-obrey" --dry-run
```

백업 폴더의 `manifest.json`에는 생성·교체·제거 목록이 있고,
`files/`에는 실제로 덮어쓰기 전의 파일이 있습니다.
`INSTALL.cmd`는 Windows에서 직접 실행 시험하지 않았고,
그 안에서 호출하는 Python 복사 도구는 호스트에서 시험했습니다.

### 수동 적용

내용물을 기존 저장소 루트에 복사하되 `.github`도 포함합니다.
이전 실험 패치를 설치했다면 원래 생성했던 다음 파일이 남지 않아야 합니다.
백업 도구는 알려진 생성 파일인지 확인한 후에만 제거합니다.

- 루트 `zephyr/module.yml` 또는 `zephyr/module.yaml`
- `.github/workflows/obrey-combo-boot-build.yml`
- 루트 `dts/bindings/behaviors/zmk,behavior-obrey-combo-boot.yaml`
- 이전 `tools/check_obrey_combo.py`, `tools/obrey_combo_patchlib.py`

이번 확장의 유효 위치는 **`local-modules/obrey-combo-boot/` 안쪽**입니다.
루트 `zephyr/module.yml`을 다시 만들면 빌드 작업 폴더가 바뀔 수 있어
원본의 고정 모듈 경로와 충돌합니다. 검사기는 이를 감지하면 중단합니다.

## 검사와 검증 한계

```powershell
py -3 scripts\validate.py
py -3 scripts\check_combo_boot.py
py -3 scripts\selftest.py
py -3 -m unittest discover -s tests -p "test_*.py" -v
```

C 컴파일러가 있는 Linux/GitHub Actions에서는 다음도 실행합니다.

```sh
python3 tests/run_host_tests.py
```

자세한 실제 실행 결과는 `VALIDATION.md`와 `reports/`에 있습니다.
소스 검사·모의 transport C 시험은 실제 Zephyr/ARM 컴파일이나 무선 연결 시험이 아닙니다.
이 ZIP에는 `west.yml`이 참조하는 외부 ZMK/하드웨어 소스 및 ARM SDK가 없으며,
이 작업 환경에서도 확보하지 못했습니다. 따라서 실제 빌드는 Actions에서 확인해야 합니다.

Keymap Editor에서는 일반 키를 편집할 수 있도록 원본 두 JSON을 유지했습니다.
새 `boot135`/`boot680`은 사용자 정의 동작이므로 일반 `&bootloader`로 바꾸지 마세요.
그 에디터의 실제 열기/저장 왕복 시험은 아직 실행하지 않았습니다.

## 출처와 원본 표시

원본 `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md`, `LICENSES/`를 유지합니다.
원본의 과거 검사 보고서는 `reference/UPSTREAM_VALIDATION.md`에 별도 보관했습니다.
기술 문서와 접근·검증 범위는 `SOURCES.md`에 있습니다.
