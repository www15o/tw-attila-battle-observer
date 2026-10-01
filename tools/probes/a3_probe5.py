#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_probe5.py — 索引侧查询：fields(基址寄存器+偏移) 与 enclosing-function/字符串/调用者。只读。
用法:
  python tools/probes/a3_probe5.py field <base_off_hex> [<off_hex> ...]   # 查 fields 表
  python tools/probes/a3_probe5.py ctx <addr> [...]                        # 函数+字符串+调用者
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DB = os.path.join(ROOT, "re", "index", "attila_index.sqlite")
db = sqlite3.connect(DB)
mode = sys.argv[1]

if mode == "schema":
    for (n, s) in db.execute("select name, sql from sqlite_master where type='table'"):
        print(s, "\n")
elif mode == "fields":
    # fields 表里 offset 的编码方式未知：先列样本
    for row in db.execute("select * from fields limit 12"):
        print(row)
elif mode == "field":
    offs = [int(x, 16) for x in sys.argv[2:]]
    cols = [r[1] for r in db.execute("PRAGMA table_info(fields)")]
    print("cols:", cols)
    for o in offs:
        q = "select * from fields where off=? order by addr"
        rows = list(db.execute(q, (o,)))
        print("=== off=0x%x : %d" % (o, len(rows)))
        for r in rows[:80]:
            print("   ", r)
elif mode == "ctx":
    for addr in [int(x, 16) for x in sys.argv[2:]]:
        f = db.execute("select id,name,start,end from functions where ? between start and end",
                       (addr,)).fetchone()
        print("--- 0x%x -> fn %s" % (addr, f))
        if not f:
            continue
        fid, name, st, en = f
        for sva, sval in db.execute(
                "select s.addr, s.value from str_refs sr join strings s on s.id=sr.string_id "
                "where sr.function_id=? limit 40", (fid,)):
            print("   str 0x%08x %r" % (sva, sval[:90]))
        print("   callers:")
        for (ca,) in db.execute("select addr from calls where callee=? limit 20", (st,)):
            print("     0x%08x" % ca)
