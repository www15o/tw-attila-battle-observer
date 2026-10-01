#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_probe3.py — 索引检索（commands/strings/calls/fields）。只读。
用法: python tools/probes/a3_probe3.py cmd <substr> | str <substr> | callers <hexaddr> | callees <hexaddr> | fn <substr>
"""
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


import os
import sqlite3
import sys

DB = os.path.join(re_dir("index"), "attila_index.sqlite")
con = sqlite3.connect(DB)
cur = con.cursor()
mode = sys.argv[1]
arg = sys.argv[2] if len(sys.argv) > 2 else ""

if mode == "cmd":
    for r in cur.execute("SELECT name,kind,addr,meta FROM commands WHERE project='attila' AND name LIKE ?",
                         ("%" + arg.upper() + "%",)):
        print(r)
elif mode == "str":
    for r in cur.execute("SELECT addr,val,nref FROM strings WHERE project='attila' AND lower(val) LIKE ? LIMIT 120",
                         ("%" + arg.lower() + "%",)):
        print(r[0], "|", r[1][:160], "|", r[2])
elif mode == "strfn":
    rows = cur.execute("SELECT addr,val FROM strings WHERE project='attila' AND lower(val) LIKE ?",
                       ("%" + arg.lower() + "%",)).fetchall()
    for a, v in rows[:40]:
        fr = [x[0] for x in cur.execute("SELECT fn FROM str_refs WHERE project='attila' AND str_addr=?", (a,))]
        print(a, "|", v[:120], "|", fr[:8])
elif mode == "callers":
    for r in cur.execute("SELECT caller FROM calls WHERE project='attila' AND callee=?", (arg.lower(),)):
        print(r[0])
elif mode == "callees":
    for r in cur.execute("SELECT callee FROM calls WHERE project='attila' AND caller=?", (arg.lower(),)):
        print(r[0])
elif mode == "fn":
    for r in cur.execute("SELECT addr,name,size FROM functions WHERE project='attila' AND name LIKE ?",
                         ("%" + arg + "%",)):
        print(r)
elif mode == "fnsize":
    for r in cur.execute("SELECT addr,name,size FROM functions WHERE project='attila' AND addr=?", (arg.lower(),)):
        print(r)
elif mode == "contains":
    t = int(arg, 16)
    best = None
    for a, n, sz in cur.execute("SELECT addr,name,size FROM functions WHERE project='attila'"):
        ia = int(a, 16)
        if ia <= t and sz and t < ia + sz:
            if best is None or ia > best[0]:
                best = (ia, n, sz)
    print("0x%08x  name=%s  size=%s  end=0x%08x" % (best[0], best[1], best[2], best[0] + best[2])
          if best else "not found")
