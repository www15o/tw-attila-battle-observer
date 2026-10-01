#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""attila_cmd_tables.py — 静态导出阿提拉引擎 CCQ/BCQ/BNCQ 命令表（名 → handler/注册点）

两种注册惯例（本轮静态实测）：
  CCQ（战役队列）: 每命令一个 119B 独立桩函数：
      push name_va; mov ecx, 全局注册单例; ...; mov [ESP+0x18], imm=handler; call reg
      → handler 是 .text 直接函数地址。
  BCQ/BNCQ（战斗队列）: 32B 等距内联注册块（单个大函数体内）：
      6a 00 | 68 <name_va> | 68 <arg2> | e8 <registrar> | 83 c4 10 | c3
      → arg2 = 该命令的原型全局对象（.bss，运行时构造）；registrar 全族共享。
      handler 语义 = 原型对象 vtable[Execute]（构造代码引用全局者→ctor→vtable，可后续静态展开；
      本轮先锁 名→注册点→原型地址→registrar 四元组）。

用法：python attila_cmd_tables.py
输出：re/attila_out/{ccq,bcq,bncq}_table.txt + 统计行。
"""
import os
import re
import sqlite3
import struct

import os  # 解析器需要；若文件已 import os，重复无害
# 本仓库不附带任何游戏二进制。DLL 路径解析优先级：
#   ATTILA_DLL（完整文件路径）→ ATTILA_DIR（游戏根目录）→ Steam 安装位置自动探测
_DLL_NAME = "empire.retail.dll"
_GAME_SUBPATH = os.path.join("steamapps", "common", "Total War Attila")


def _steam_roots():
    """列出本机 Steam 库根目录（注册表 + libraryfolders.vdf）；非 Windows / 失败返回空表。"""
    roots = []
    try:
        import winreg
    except ImportError:
        return roots
    steam = None
    for hive, key, name in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    ):
        try:
            with winreg.OpenKey(hive, key) as k:
                steam = winreg.QueryValueEx(k, name)[0]
                break
        except OSError:
            continue
    if not steam:
        return roots
    steam = os.path.normpath(steam)
    roots.append(steam)
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    try:
        with open(vdf, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.startswith('"path"'):
                    parts = line.split('"')
                    if len(parts) >= 4:
                        p = parts[3].replace(chr(92) * 2, chr(92))  # 反斜杠用 chr(92) 写，免去转义层数
                        if os.path.isdir(p):
                            roots.append(os.path.normpath(p))
    except OSError:
        pass
    return roots


def find_dll():
    """定位游戏引擎模块；找不到返回 None（保持模块可 import，不猜路径）。"""
    env = os.environ.get("ATTILA_DLL")
    if env and os.path.isfile(env):
        return env
    cands = []
    d = os.environ.get("ATTILA_DIR")
    if d:
        cands.append(os.path.join(d, _DLL_NAME))
    for root in _steam_roots():
        cands.append(os.path.join(root, _GAME_SUBPATH, _DLL_NAME))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def _repo_root():
    """从本文件向上找到含 tools/ 的目录（tools/ 与 tools/probes/ 都适用）。"""
    p = os.path.dirname(os.path.abspath(__file__))
    while os.path.dirname(p) != p:
        if os.path.isdir(os.path.join(p, "tools")):
            return p
        p = os.path.dirname(p)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def re_dir(sub):
    """逆向工作目录：环境变量可覆盖，默认仓库内 re/<sub>（不一定存在，工具自己建）。"""
    env = os.environ.get("ATTILA_RE_" + sub.upper())
    return env or os.path.join(_repo_root(), "re", sub)


BIN = find_dll()
DB = os.path.join(re_dir("index"), "attila_index.sqlite")
OUT = re_dir("attila_out")
BASE = 0x10000000


def load_sections():
    with open(BIN, "rb") as f:
        data = f.read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    optsz = struct.unpack_from("<H", data, e + 20)[0]
    secs = []
    p = e + 24 + optsz
    for i in range(nsec):
        name = data[p:p + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, p + 8)
        secs.append((name, vaddr, min(vsize, rawsize), rawptr))
        p += 40
    return data, secs


def va2raw(secs, va):
    r = va - BASE
    for _n, vaddr, rsize, rawptr in secs:
        if vaddr <= r < vaddr + rsize:
            return rawptr + (r - vaddr)
    return None


def raw_scan_pointers_to(data, secs, target_va, regions=(".text", ".rdata", ".data")):
    hits = []
    needle = struct.pack("<I", target_va)
    for n, vaddr, rsize, rawptr in secs:
        if n not in regions:
            continue
        blob = data[rawptr:rawptr + rsize]
        start = 0
        while True:
            i = blob.find(needle, start)
            if i < 0:
                break
            if (rawptr + i) % 4 == 0:
                hits.append(BASE + vaddr + i)
            start = i + 1
    return hits


def main():
    os.makedirs(OUT, exist_ok=True)
    data, secs = load_sections()
    txt = [s for s in secs if s[0] == ".text"][0]
    TLO, THI = BASE + txt[1], BASE + txt[1] + txt[2]
    con = sqlite3.connect(DB)
    cur = con.cursor()

    def strs(pref):
        rows = cur.execute(
            "SELECT addr,val FROM strings WHERE project='attila' AND val LIKE ?",
            ("%" + pref + "%",)).fetchall()
        out = []
        for a, v in rows:
            m = re.fullmatch(rf'{re.escape(pref)}[A-Z0-9_]+', v.strip('"'))
            if m:
                out.append((int(a, 16), m.group(0)))
        return sorted(set(out))

    for pref in ("CCQ_", "BCQ_", "BNCQ_"):
        names = strs(pref)
        rows = []
        orphan = []
        for va, name in names:
            fns = [r[0] for r in cur.execute(
                "SELECT fn FROM str_refs WHERE project='attila' AND str_addr=?", (hex(va),))]
            found = False
            # 1) 独立桩函数模式：桩内 C7 44 24 disp imm32（imm ∈ .text）= handler
            for fn in fns:
                fe = int(fn, 16)
                fr = va2raw(secs, fe)
                if fr is None:
                    continue
                blob = data[fr:fr + 160]
                hs, i = [], 0
                while True:
                    i = blob.find(b"\xc7\x44\x24", i)
                    if i < 0:
                        break
                    imm = struct.unpack_from("<I", blob, i + 4)[0]
                    if TLO <= imm < THI:
                        hs.append(imm)
                    i += 4
                if hs:
                    rows.append((name, "stub", fe, sorted(set(hs)), None))
                    found = True
            if found:
                continue
            # 2) 内联注册块模式（push 后 dword==name VA 处）：arg2@+4(+5)，registrar@+9(+10)
            ptrs = raw_scan_pointers_to(data, secs, va)
            for p in [x for x in ptrs if TLO <= x < THI]:
                rp = va2raw(secs, p)
                if rp is None or data[rp - 1] != 0x68 or data[rp + 4] != 0x68:
                    continue
                arg2 = struct.unpack_from("<I", data, rp + 5)[0]
                reg = None
                if data[rp + 9] == 0xE8:
                    rel = struct.unpack_from("<i", data, rp + 10)[0]
                    reg = (p + 14 + rel) & 0xFFFFFFFF
                kind = "inline_text" if TLO <= arg2 < THI else "inline_global"
                rows.append((name, kind, p, [arg2], reg))
                found = True
                break
            if not found:
                orphan.append((name, [hex(p) for p in ptrs[:4]]))
        fn_out = os.path.join(OUT, pref.strip("_").lower() + "_table.txt")
        with open(fn_out, "w", encoding="utf-8") as f:
            f.write("# name \t kind \t site \t imm/handler(s) \t registrar\n"
                    "# kind: stub=独立119B桩(handler imm) / inline_global=内联注册块(arg2=原型全局,registrar=共享注册函数)\n")
            for name, kind, site, imms, reg in sorted(rows):
                f.write(f"{name}\t{kind}\t0x{site:08x}\t" +
                        ",".join("0x%08x" % h for h in imms) +
                        ("\t0x%08x" % reg if reg else "\t-") + "\n")
            if orphan:
                f.write("\n# --- unresolved (inspect) ---\n")
                for name, ps in sorted(orphan):
                    f.write(f"{name}\trefs={','.join(ps)}\n")
        nstub = sum(1 for r in rows if r[1] == "stub")
        nlin = sum(1 for r in rows if r[1] != "stub")
        regs = sorted({r[4] for r in rows if r[4]})
        print(f"[{pref}] named={len(names)} stub={nstub} inline={nlin} orphan={len(orphan)} "
              f"registrars={['0x%x' % x for x in regs[:4]]} -> {os.path.basename(fn_out)}")


if __name__ == "__main__":
    main()
