#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_scanfield.py — 在 .text 中扫描形如 [reg+0x<disp32>] 的字段访问（按字节模式定位后反汇编确认）。
只读。用法: python tools/a3_scanfield.py <off_hex> [off_hex ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a3_dis as A
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

_t = next(s for s in A._SECS if s["name"] == ".text")
BASE = _t["va"]                      # .text 的虚拟地址（不是镜像基！）
SIZE = A._DATA[_t["rawptr"]: _t["rawptr"] + _t["rawsize"]]
c = Cs(CS_ARCH_X86, CS_MODE_32)

for spec in sys.argv[1:]:
    if spec.endswith("h"):
        spec = spec[:-1]
    val = int(spec, 16)
    pat = val.to_bytes(4, "little")
    print("=== disp32 = 0x%x (pattern %s) ===" % (val, pat.hex()))
    pos = 0
    n = 0
    while True:
        k = SIZE.find(pat, pos)
        if k < 0:
            break
        pos = k + 1
        # 尝试从 k-8..k-1 起各偏移反汇编，找跨越该模式的指令
        best = None
        for back in range(1, 10):
            st = k - back
            if st < 0:
                continue
            for ins in c.disasm(SIZE[st:st + 16], BASE + st, 1):
                if ins.address <= BASE + k and BASE + k + 4 <= ins.address + len(ins.bytes):
                    if "0x%x" % val in ins.op_str or "+ %d" % val in ins.op_str:
                        best = ins
                    break
            if best:
                break
        if best is None:
            print("   0x%08x:  <no insn> %s" % (BASE + k, SIZE[max(0, k - 8):k + 8].hex(" ")))
            n += 1
            continue
        print("   0x%08x: %-22s %s %s" % (best.address, best.bytes.hex(), best.mnemonic, best.op_str))
        n += 1
    print("--- total raw hits: %d" % n)
