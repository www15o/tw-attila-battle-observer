# 目标3 探索地图（33_GOAL3_EXPLORATION_MAP）— 阿提拉

| 路线 | 状态 | 依据/备注 |
|---|---|---|
| **R-1A 分叉输入直写（s2 b9 复刻）** | 🟡 静态画像完成，创建/挂接链未闭合 | Attila 版分叉输入=**PENDING_BATTLE* 内嵌的 FACTION_VOTE 记录 (+0x10 就绪 /+0x11 人类) 字节对**（`10b54580` 的 `0x1b4` 对象与 `PENDING_BATTLE` 类型描述已锁；stride 0x20 数组，真身状态机 `0x10b87d20`）——比 s2 单字节复杂：需要「找到/伪造一条记录」而非「写一字节」。弱校验为 count@+0x08、begin@+0x0c、state@+0x0c、ready/human@+0x10/+0x11；`+0x18/+0x1c` 不赋予 timeout/type 语义。下一步=**堆扫 Campaign Model vtable 指针**（ctor `0x10763710` 首条 `mov [ebx],0x11B1FE54`，运行时值=模块基址+0x1B1FE54）→ 活实例 `+0x1c38`（pending 槽）→ `pending+0xd4` → 投票系统 → count@+0x08/begin@+0x0C/记录数组——**一次扫描同时给 Goal2/Goal3 上根**；`109b50d0` 只作二级 accessor，不再作根。另有静态生命周期链 `upper(vtable 0x11b25144)+0x1f41d4 ↔ Campaign_ENV+0x28 → Campaign Model`，但最终外部根和 live new/attach/replace 时序仍待实机。 |
| **R-1B 加载判定函数强制返回值（3K fork6o 复刻）** | ✅ 加载打通（2026-09-06）；精修待实机（规模筛选+退出保底，2026-09-07） | `[F]` `10b9da20→10bc7ce0` 锁到 state 3/4/6；运行时 patch `0x10B9DA20` 返回 0 → AI-only pending `+0x38` 1→4 → 进入 AI-vs-AI 战场，用户确认可见双方交战。精修静态已备：规模条件桩（`P+0x48/P+0x4C` + `FUN_10BADB10`）与 ESC 退出 builder A 路由（`0x1016e449`），探针/场景 54/55 待实机。 |
| **R-2 伪造人类足迹** | ⬜未探 | 高成本兜底 |
| **R-3 回放/自动存档观看（replay 路线）** | ⬜未探 | s2 有 replay 判活记录（03 §31/ESF 明文树）；Attila 回放格式同源概率高（ESF），可做「不求实时观战」兜底 |
| **R-4 GFB 无玩家军队实验（官方翻盘点，★002 新增）** | ⬜未探 | Attila 自带 `generated_battle:new(..., prevent_deployment, ...)` + `bm:setup_battle` 官方战斗加载框架（实验 002 实证）——关键问题=「玩家无军队的 GFB 战」是否加载/旁观。若成=目标3 走通道①免引擎层；引擎侧用 Ghidra 反查 GFB 加载谓词先行评估 |

判据：M1 pending/分叉锚静态锁定 → M2 实机触发一场 AI 内战加载 → M3 旁观可看完整战斗。
