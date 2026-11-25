"""Headless libretro host for Beetle PSX HW (software renderer).

Runs the core in-process, exposes a JSON-over-TCP control port:
  {"cmd":"run","frames":N}                    -> run N frames
  {"cmd":"buttons","hold":["start","a"]}      -> set held retropad buttons (persist)
  {"cmd":"tap","btn":"a","frames":3}          -> press btn for N frames then release
  {"cmd":"read","addr":"8013b1ec","len":4}    -> read RAM (hex string reply)
  {"cmd":"write","addr":"...","hex":"AABB"}   -> write RAM
  {"cmd":"run_until","addr":"...","len":1,"neq":"70","max":600}
        run frames until mem[addr:len] != initial (or == "eq" value), report frames run
  {"cmd":"trace","addr":"8013b1e8","len":8,"frames":N}  -> per-frame samples
  {"cmd":"shot","path":"x.png"}               -> dump current frame as PNG
  {"cmd":"save","path":"x.state"} / {"cmd":"load","path":"x.state"}
  {"cmd":"quit"}
"""
import ctypes as C
import json, os, socket, struct, sys, zlib, threading, time

CORE = os.environ.get("MEDNAFEN_CORE", "mednafen_psx_hw_libretro.dll")
HERE = os.path.dirname(os.path.abspath(__file__))
SYSDIR = os.path.join(HERE,"..","system").encode()
SAVEDIR = os.path.join(HERE,"..","saves").encode()
GAME = os.environ["GAME"].encode()
PORT = int(os.environ.get("PORT", "46600"))

os.makedirs(SAVEDIR.decode(), exist_ok=True)

# ---- libretro types ----
env_t = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
video_t = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
audio_t = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
audio_batch_t = C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
input_poll_t = C.CFUNCTYPE(None)
input_state_t = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

class retro_game_info(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.c_void_p),
                ("size", C.c_size_t), ("meta", C.c_char_p)]

class retro_variable(C.Structure):
    _fields_ = [("key", C.c_char_p), ("value", C.c_char_p)]

class retro_system_av_info(C.Structure):
    _fields_ = [("base_w", C.c_uint), ("base_h", C.c_uint),
                ("max_w", C.c_uint), ("max_h", C.c_uint), ("aspect", C.c_float),
                ("fps", C.c_double), ("sample_rate", C.c_double)]

RETRO_MEMORY_SYSTEM_RAM = 2

BTN = {"b":0,"y":1,"select":2,"start":3,"up":4,"down":5,"left":6,"right":7,
       "a":8,"x":9,"l":10,"r":11,"l2":12,"r2":13}

# ---- state ----
held = set()          # retropad ids held
tap_queue = []        # (id, frames_remaining)
pixfmt = [0]          # 0=0RGB1555 1=XRGB8888 2=RGB565
frame = {"data": None, "w": 0, "h": 0, "pitch": 0}
var_store = {}        # keep c_char_p alive
VARS = {
    b"beetle_psx_hw_renderer": b"software",
    b"beetle_psx_hw_skip_bios": b"enabled",
    b"beetle_psx_hw_cd_fastload": b"2x(native)",
    b"beetle_psx_hw_cdimagecache": b"enabled",
}
unknown_keys = set()

def log(*a):
    print(*a, file=sys.stderr, flush=True)

@env_t
def env_cb(cmd, data):
    c = cmd & 0xFFFF
    if c == 3:   # GET_CAN_DUPE
        C.cast(data, C.POINTER(C.c_bool))[0] = True
        return True
    if c == 9:   # GET_SYSTEM_DIRECTORY
        C.cast(data, C.POINTER(C.c_char_p))[0] = SYSDIR
        return True
    if c == 31:  # GET_SAVE_DIRECTORY
        C.cast(data, C.POINTER(C.c_char_p))[0] = SAVEDIR
        return True
    if c == 10:  # SET_PIXEL_FORMAT
        pixfmt[0] = C.cast(data, C.POINTER(C.c_uint))[0]
        return True
    if c == 15:  # GET_VARIABLE
        var = C.cast(data, C.POINTER(retro_variable))
        key = var[0].key
        if key in VARS:
            var[0].value = VARS[key]
            return True
        unknown_keys.add(key)
        return False
    if c == 17:  # GET_VARIABLE_UPDATE
        C.cast(data, C.POINTER(C.c_bool))[0] = False
        return True
    if c in (16, 53, 54, 67, 68):  # SET_VARIABLES / CORE_OPTIONS*
        return True
    if c in (11, 13, 35, 36, 37, 44, 55, 65, 66, 69):
        return True
    if c == 52:  # GET_CORE_OPTIONS_VERSION
        C.cast(data, C.POINTER(C.c_uint))[0] = 2
        return True
    if c == 39:  # GET_LANGUAGE
        C.cast(data, C.POINTER(C.c_uint))[0] = 0
        return True
    if c == 48:  # GET_AUDIO_VIDEO_ENABLE
        C.cast(data, C.POINTER(C.c_int))[0] = 3
        return True
    return False

@video_t
def video_cb(data, w, h, pitch):
    if data:
        frame["data"] = C.string_at(data, pitch * h)
        frame["w"], frame["h"], frame["pitch"] = w, h, pitch

@audio_t
def audio_cb(l, r):
    pass

@audio_batch_t
def audio_batch_cb(data, frames):
    return frames

@input_poll_t
def input_poll_cb():
    pass

@input_state_t
def input_state_cb(port, device, index, id_):
    if port != 0 or device != 1:  # RETRO_DEVICE_JOYPAD
        return 0
    if id_ in held:
        return 1
    for tid, n in tap_queue:
        if tid == id_ and n > 0:
            return 1
    return 0

core = C.CDLL(CORE)
core.retro_get_memory_data.restype = C.c_void_p
core.retro_get_memory_size.restype = C.c_size_t
core.retro_serialize_size.restype = C.c_size_t
core.retro_serialize.restype = C.c_bool
core.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]
core.retro_unserialize.restype = C.c_bool
core.retro_unserialize.argtypes = [C.c_void_p, C.c_size_t]
core.retro_load_game.restype = C.c_bool

core.retro_set_environment(env_cb)
core.retro_set_video_refresh(video_cb)
core.retro_set_audio_sample(audio_cb)
core.retro_set_audio_sample_batch(audio_batch_cb)
core.retro_set_input_poll(input_poll_cb)
core.retro_set_input_state(input_state_cb)
core.retro_init()

gi = retro_game_info(GAME, None, 0, None)
if not core.retro_load_game(C.byref(gi)):
    log("retro_load_game FAILED")
    sys.exit(1)
log("game loaded")

av = (C.c_uint8 * C.sizeof(retro_system_av_info))()
core.retro_get_system_av_info(C.byref(av))

ram_ptr = core.retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM)
ram_size = core.retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM)
log(f"RAM ptr={ram_ptr:#x} size={ram_size:#x}  unknown_vars={sorted(unknown_keys)}")
RAM = (C.c_uint8 * ram_size).from_address(ram_ptr)

def mem_read(addr, n):
    a = addr & 0x1FFFFF
    return bytes(RAM[a:a+n])

def mem_write(addr, data):
    a = addr & 0x1FFFFF
    RAM[a:a+len(data)] = list(data)

def step(n=1):
    for _ in range(n):
        core.retro_run()
        for i in range(len(tap_queue)-1, -1, -1):
            tid, fr = tap_queue[i]
            fr -= 1
            if fr <= 0:
                tap_queue.pop(i)
            else:
                tap_queue[i] = (tid, fr)

def png_write(path):
    d, w, h, pitch = frame["data"], frame["w"], frame["h"], frame["pitch"]
    if not d:
        return "no frame"
    rows = []
    fmt = pixfmt[0]
    for y in range(h):
        row = bytearray([0])
        base = y * pitch
        for x in range(w):
            if fmt == 1:
                px = struct.unpack_from("<I", d, base + x*4)[0]
                row += bytes(((px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF))
            elif fmt == 2:
                px = struct.unpack_from("<H", d, base + x*2)[0]
                row += bytes((((px >> 11) & 31) << 3, ((px >> 5) & 63) << 2, (px & 31) << 3))
            else:
                px = struct.unpack_from("<H", d, base + x*2)[0]
                row += bytes((((px >> 10) & 31) << 3, ((px >> 5) & 31) << 3, (px & 31) << 3))
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 6)
    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", raw) + chunk(b"IEND", b""))
    open(path, "wb").write(png)
    return f"ok {w}x{h}"

def handle(req):
    cmd = req.get("cmd")
    if cmd == "run":
        step(req.get("frames", 1))
        return {"ok": True}
    if cmd == "buttons":
        held.clear()
        held.update(BTN[b] for b in req.get("hold", []))
        return {"ok": True, "held": sorted(held)}
    if cmd == "tap":
        tap_queue.append((BTN[req["btn"]], req.get("frames", 3)))
        if req.get("run"):
            step(req.get("run"))
        return {"ok": True}
    if cmd == "read":
        a = int(req["addr"], 16)
        return {"ok": True, "hex": mem_read(a, req.get("len", 4)).hex()}
    if cmd == "write":
        a = int(req["addr"], 16)
        mem_write(a, bytes.fromhex(req["hex"]))
        return {"ok": True}
    if cmd == "run_until":
        a = int(req["addr"], 16); n = req.get("len", 1)
        mx = req.get("max", 600)
        eq = bytes.fromhex(req["eq"]) if "eq" in req else None
        init = mem_read(a, n)
        for i in range(mx):
            step(1)
            cur = mem_read(a, n)
            if eq is not None:
                if cur == eq:
                    return {"ok": True, "frames": i+1, "hex": cur.hex(), "hit": True}
            elif cur != init:
                return {"ok": True, "frames": i+1, "hex": cur.hex(), "hit": True}
        return {"ok": True, "frames": mx, "hex": mem_read(a, n).hex(), "hit": False}
    if cmd == "trace":
        a = int(req["addr"], 16); n = req.get("len", 4)
        out = []
        for _ in range(req.get("frames", 60)):
            step(1)
            out.append(mem_read(a, n).hex())
        return {"ok": True, "samples": out}
    if cmd == "shot":
        return {"ok": True, "result": png_write(req["path"])}
    if cmd == "save":
        sz = core.retro_serialize_size()
        buf = C.create_string_buffer(sz)
        if not core.retro_serialize(buf, sz):
            return {"ok": False, "err": "serialize failed"}
        open(req["path"], "wb").write(buf.raw)
        return {"ok": True, "size": sz}
    if cmd == "load":
        data = open(req["path"], "rb").read()
        ok = core.retro_unserialize(data, len(data))
        return {"ok": bool(ok)}
    if cmd == "eval":
        g = {"mem_read": mem_read, "mem_write": mem_write, "step": step, "held": held, "BTN": BTN, "core": core, "C": C, "frame": frame, "png_write": png_write, "tap_queue": tap_queue}
        exec(req["code"], g)
        return {"ok": True, "result": g.get("result")}
    if cmd == "quit":
        return {"ok": True, "quit": True}
    return {"ok": False, "err": f"unknown cmd {cmd}"}

log("warming up 30 frames...")
step(30)
log("listening on port %d" % PORT)

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", PORT))
srv.listen(1)
while True:
    conn, _ = srv.accept()
    f = conn.makefile("rwb")
    try:
        for line in f:
            try:
                req = json.loads(line)
                resp = handle(req)
            except Exception as e:
                resp = {"ok": False, "err": repr(e)}
            f.write((json.dumps(resp) + "\n").encode())
            f.flush()
            if resp.get("quit"):
                sys.exit(0)
    except (ConnectionError, OSError):
        pass
    finally:
        conn.close()
