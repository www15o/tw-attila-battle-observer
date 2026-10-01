# 目标1 探索地图（13_GOAL1_EXPLORATION_MAP）— 阿提拉

> 指挥地图：目标→路线→技术路径→证据/行动。开工认领一条路径，卡住回来换路（根 AGENTS §5）。

## 目标1 = 玩家部队交**原生**战斗 AI 指挥（观战友好、质量=友军 AI）

| 路线 | 状态 | 依据/备注 |
|---|---|---|
| **R-A 官方 scripting.lua 交 AI** | ⬜未探 | 已知先例存在（Steam mod「Attila 原版 AI general」）；但按 s2/70 铁证属**脚本型 AI**——只能当观测通道/对照组，非达成验收 |
| **R-B 引擎字段直写（s2 同款）** | 🟡静态进行中 | 前提=实验 001 证实同源标记族存在；技术路径：①re_toolkit 建 attila Ghidra 工程 ②由 BCQ/命令串锚定军队对象 ③差分人类军 vs AI 军字段 ④实机直写 |
| **R-C 命令注入（BCQ handler 直调）** | ⬜未探 | s2 时代 BCQ 直调实机失败（TLS 崩溃）；Attila 若有 Lua 控制台（TWASE/ConsulScriptum）则优先级升——可引擎内调脚本 API |

## 里程碑判据

- M1 静态锁定命令注册表/军队字段候选（Ghidra+差分）
- M2 观测闭环（Lua 控制台或 hook，校准见根 §3）
- M3 实机接管一次（原生 AI 指挥玩家军打完一仗）
