#!/bin/bash
# restart headless emulator with Korean build (background). usage: tools/restart.sh [cue]
cd "$(dirname "$0")/.."
python -c "
import sys;sys.path.insert(0,'tools')
from emu import Emu
try: Emu()(cmd='quit')
except Exception: pass
" 2>/dev/null
sleep 2
CUE="${1:-../Lunatic Dawn III (Korean).cue}"
MEDNAFEN_CORE="$(cygpath -w tools/mednafen_psx_hw_libretro.dll)" GAME="$(cygpath -w "$CUE")" PORT=46677 nohup python tools/host.py > host.log 2>&1 &
sleep 6; tail -1 host.log
