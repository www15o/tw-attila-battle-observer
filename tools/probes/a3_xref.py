#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a3_xref.py — 原始交叉引用（含未对齐立即数）+ 命中点反汇编上下文。只读。
用法: python tools/probes/a3_xref.py <hexva> [context_insns=12]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import a3_dis as A
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

tgt = int(sys.argv[1], 16)
ctx = int(sys.argv[2]) if len(sys.argv) > 2 else 12
hits = A.xref(tgt)
print("target=0x%08x hits=%d" % (tgt, len(hits)))
c = Cs(CS_ARCH_X86, CS_MODE_32)
for va, sec, aligned in hits:
    print("\n--- 0x%08x in %s aligned=%s ---" % (va, sec, aligned))
    if sec != ".text":
        print("   bytes:", A.read(va - 16, 48).hex(" "))
        continue
    start = va - ctx * 3
    buf = A.read(va - 40, 120)
    for i in c.disasm(buf, va - 40):
        if tgt - 12 <= i.address <= tgt + 60 or abs(i.address - va) < 48:
            print("   0x%08x: %-24s %-7s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
