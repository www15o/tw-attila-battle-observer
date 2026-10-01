# 目标2 探索地图（23_GOAL2_EXPLORATION_MAP）— 阿提拉

说明：文中出现的 work/ 、testkit/ 、experiments/ 、outputs/ 、research/ 、extract/ 、re/ 等路径指作者私有工作目录，未随本库公开。

| 路线 | 状态 | 依据/备注 |
|---|---|---|
| **R-A 官方控制台/Lua** | 🟡 候选保留 | `grant_faction_handover`、`set_cai_faction_manager(s)` 有字符串/命令表迹象，但 callback/参数/效果未锁，不能当成 LocalFaction 或已证通道 |
| **R-B startpos.esf 编辑** | ⬜未探 | 把玩家派系 manager 改全 AI 能否绕开人类门（s2 经验：manager≠人类开关，预期不完整，但可能减少引擎层工作量） |
| **R-C 引擎字段直写（s2 两段式）** | ✅ 实机闭环 2026-09-07 | CAI 行 `+0x84c=1`=人控；`CM+0x1c44` manager 表 HUMAN(6)→FULL_MANAGER(0)；东哥特实测成功。工具：`work/attila_control.py` + `work/g2_switch_to_ai.py` |
| **R-D hotseat 旁路** | ❌关闭 | LocalFaction/hotseat/dropout 未形成 CAI 接管链；不再投入实机 |

判据：M1 静态锚点齐（人类标志/manager 表候选）→ M2 观测（回合推进+AI 行为日志）→ M3 实机看海 ≥10 回合有行动（招募/外交/进军）。
