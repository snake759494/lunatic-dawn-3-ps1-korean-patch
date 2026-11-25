# 직접 빌드하기

## 준비물
- 원본 디스크 이미지 (README의 해시와 일치), 저장소의 상위 폴더에 원래 이름으로 (`../Lunatic Dawn III (Japan) (Track 1).bin`, `(Track 2).bin`)
- Python 3.12 이상, `pip install pillow numpy capstone`
- 글꼴: `docs/FONT_CREDITS.md` 참고
- 번역 대본 `work/tr/*_ko.json` (저장소 미포함). 저장소 루트에 `work/` 를 만들고 `tools/` 를 그 안에서 실행합니다.

## 순서
1. 파일 추출: `python tools/extract.py` → `work/ext/`
2. 문자열 추출: `python tools/extract_text.py` → `work/text/*.json`
3. 번역 대본을 `work/tr/*_ko.json` 에 같은 ID로 작성
4. 빌드: `python tools/build.py`
   - 글꼴(STRING1/2.TH4) 생성, MSG.DAT·ADVMSG·DATMODL·REQUEST·GAME.BIN 재구성, 오버레이·실행 파일 문자열, 타이틀 그림을 처리하고 `Lunatic Dawn III (Korean) (Track 1).bin/.cue` 를 만듭니다.
5. 검사: `python tools/verify.py`, `python tools/hilo_check.py`, `python tools/trcheck.py`
6. xdelta: `xdelta3 -e -0 -s 원본.bin 결과.bin 패치.xdelta`

## 검수 도구
- `tools/host.py` — 헤드리스 libretro(mednafen PSX) 호스트. `MEDNAFEN_CORE`, `GAME`, `PORT` 환경 변수를 씁니다. BIOS는 `work/system/` 에.
- `tools/emu.py`, `tools/play.py`, `tools/pg.py` — 버튼 입력·스크린샷·상태저장
- `tools/explore.py`, `tools/bfs.py` — 상태저장을 이용한 이동 가능 경로 탐색
- `tools/hotpatch.py` — 새 빌드의 바뀐 바이트를 실행 중 RAM에 덮어써 바로 확인
