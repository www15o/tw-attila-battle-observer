# 目标3 机制地图（31_GOAL3_MECHANISM_MAP）— 阿提拉：观看 AI 势力内战

说明：文中出现的 work/ 、testkit/ 、experiments/ 、outputs/ 、research/ 、extract/ 、re/ 等路径指作者私有工作目录，未随本库公开。

> 状态：**静态 M1 主链已锁定；R-1B 强制加载实机成功（2026-09-06）**。当前成立结论唯一载体 = 本文件；证伪 → `32_GOAL3_LOGBOOK.md`。

## §0 跨项目认知源（机制概念，勿重新推导）

- 幕府2 终局链（s2 40 §0 + Goal_3_LogBook 08-19，★★★达成）：看海态 pending 战斗 → **写 `[pending+0xb9]=1`**（分叉输入，1 字节外部直写）→ 状态 4 人类加载链 → env→battle_mgr 创建 → 本地玩家不在参战名单 → `0x5cf168` 自动旁观（IsSpectator=1）→ 纯 AI 互战可视。btype=`[pending+0x58]`；PRE 单位数=`[pending+0x90]+0x1c→hdr+0x18/+0x78`。
- 3K 达成（tw3k 31 §2.21，2026-08-22）：强制 `0x141861A50` 返回 0 → AI 内战加载成功（b9 等价 = 该函数返回值）→ **b9 思路已跨位数跨代验证一次**。
- 族同源静态证据（tw3k 00_INDEX 已录）：3K 保留 `PRE_BATTLE_VOTING_SYSTEM/FACTIONS_READY_TO_FIGHT/PENDING_BATTLE` 全族串。

## §1 阿提拉待找对应物

- [ ] pending battle 对象与其「人类足迹/分叉输入」字段（s2 +0xb9 等价物）——**对象类型与内部初始化已静态锁定，但 live 创建/挂接时机未闭合**：`0x10763710` 调用 `10b54580` 前分配 `0x1b4`，该函数返回原始 `this`，vtable 为 `0x11b4b3b8`，同族类型描述为 `PENDING_BATTLE`；因此 `CampaignModel+0x1c38` 是 `PENDING_BATTLE*`，其 `+0xD4` 才是内嵌投票系统。Attila 的分叉输入**不是单字节**，是 `PRE_BATTLE_VOTING_SYSTEM::FACTION_VOTE` **投票记录数组（stride 0x20）**：`+0x10`=ready 字节（READY_TO_START 命令写它）、`+0x11`=人类足迹字节、`+0xc`=状态（3=开战触发）。真身 `0x10b87d20`（全体人类就绪→开战 / 超时 / 记录删除路径）。**容器布局**：投票系统内嵌于 pending battle **+0xD4**；容器 = `this+0x08=count`、`this+0x0C=begin`，end=begin+count*0x20（非 this+0x10 end，无 vtable）。新增静态证据：`0x10b58e40` 初始化投票子对象的 capacity/count/begin；`0x10b51950` 是 `FACTION_VOTE` 记录初始化/构造例程，明确清零 `+0xc/+0x10/+0x11`，并填充 `+0x14..+0x1c`；`0x10ba16f0` 是 `VOTING_SYSTEM_BLOCK` 反序列化/扩容插入链，会按 stride 0x20 调用该记录初始化并写入 count/begin。`0x10763710` 已锁定 Campaign Model ctor，并通过 `FUN_10b54580(param_1+0x43c,1)` 写入 `manager+0x1c38`；剩余缺口仅是 live pending 的新建/attach/替换时机与实机对象同一性。

## §1b 2026-09-06 静态分工裁决

- `FUN_109b50d0()` 不能直接作为 manager 根：反汇编本体为 `return *(*(param_1)+0x28)`，它是二级 accessor。manager-like 对象的直接证据来自 `0x107f6540`：该函数以 `param_1+0x28` 访问 `+0x1c2c/+0x1c38`，并把后者送入 pending 链。更硬的 manager 槽初始化来自 `0x10763710`：`CAMPAIGN_MODEL::CAMPAIGN_MODEL` 构造阶段将 `FUN_10b54580(...)` 返回的 **`PENDING_BATTLE*`** 写入 `+0x1c38`。上层生命周期也已补齐到：`upper(vtable 0x11b25144)+0x1f41d4 ↔ Campaign_ENV`，而 `Campaign_ENV+0x28 = Campaign Model`；`10784c10/10792b00` 的析构释放链证明这不是单纯 accessor。上层具体类名、最终全局/注册表根和 live pending 的 attach/替换时机仍未证实。`109b50d0` 在 vote/pending 族中仍是重要的对象回取入口，但不再作为静态根。
- S-03 扫到的若干 `[reg+0x1c38]` 写入（byte/int 的 0/1/2/3 等）没有对象类型证明，不能命名为 manager writer；继续扩大 raw offset 扫描不合算，下一步应从 `109b50d0` 的**输入对象链**或 RTTI/vtable/ctor 结果做运行时逐跳。
- S-04 进一步锁定记录后半段：`record+0x14..+0x1B` 是被 helper/timer 使用的 8 字节不透明子状态，`+0x1C` 是只在压缩复制中的不透明 dword；`+0x18` 不能称 timeout，`+0x1C` 不能称 type。现有字段约束只能作弱校验，不能单独承担全堆扫描。
- **上层链静态收口**：`0x11b25144` 虚表的前 9 个方法均直接访问/转发 `upper+0x1f41d4`，但 `vtable-4=0x11b25140` 为 0，未见可用 MSVC COL 或独立类型 getter，因此 upper 的具体类名不能从当前 DLL 静态命名。实际生命周期是嵌套链：`外层 Campaign_ENV+0x7c → upper(size 0x1f41e4)+0x1f41d4 → 内层 Campaign_ENV(size 0x118)+0x28 → Campaign Model`；外层析构 `10782f30` 调 upper 虚析构，`10784c10/10792b00` 释放 inner ENV 与 upper。本轮反查 `106feae0/106febf0/106fecb0/106fedd0` 的上层 caller 后，ENV 返回值只进入局部或调用方提供的向量，未见固定全局/注册表保存；最终外部根和 live attach/replace 时机转为运行时逐跳问题。
- **G3-01/G3-02 静态分叉候选（2026-09-06）**：`[F]` `FUN_100d4b70()`/`FUN_10b5f310(state)` 实际通过 `PENDING_BATTLE+0x34` 的嵌套状态位置读写状态值（反编译中的 `ecx=pending+0x0d` 是该字段的 this-adjusted 入口），且在写入 `0xc` 时经 vtable 触发后续动作。`FUN_10bc7ce0()` 的 state=1 分支调用 `FUN_10b9da20()`，把结果写入 `pending+0x3c`，随后：谓词为假时写入状态 `((pending+0xbc==0)+3)`，即 `+0xbc==0 → state 4`、否则 `state 3`；谓词为真时进入 `FUN_10b72080()` 并写入 `state 6`。`10b9da20` 的输入是可复核的：`pending+0x3d/+0xa5` 门、`+0x64` participant count、`+0x68` participant 数组，记录步长 `0x10`，记录 `+0x0d` 字节，以及 `pending+0x28` 经二级 accessor 得到的 model `+0x1cc4`；特殊情况下还检查 `pending+0xd4` vote 系统。由此可把“AI-only/有人类足迹”分叉锁到一段真实状态机，而不是堆形状猜测。
- **state 4 的语义边界**：`[F]` `FUN_107f5580()` 通过 pending 的 `+0x34` 状态位置，在调用 `FUN_10bc7ce0()` 后检查 `state==4`；当 `FUN_107dbb30()==0` 且状态不是 4 时返回 `param_2={0,0}`，否则返回 `param_2={0,1}`。这证明 state 4 是该上层更新器认可的“继续/就绪”分支。`[S/U]` 结合 Goal3 路线和 s2 同源经验，state 4 很可能是 AI-only 进入战斗加载的候选状态；但当前没有从 state 4 直接反汇编到 `BATTLE_ENV` 构造或 battle_mgr/旁观入口，因此不能写成“state 4=加载已证实”。
- **G3-03 预研究边界**：`[F]` `BATTLE_ENV` 构造函数为 `0x102c8e30`，可见调用者包括 `0x100cad20/0x100cd150/0x100cd770/0x100ce490/0x102ca970/0x102e5ec0/0x102e5fc0`；`0x102ca970` 是其内部 wrapper/初始化路径。`[U]` 尚未找到 `state 4 → 0x102c8e30` 或该状态 → battle_mgr/spectator 的静态边，因此 G3-03 仍未闭合，下一步只追状态4消费者/调用者，不再扩大无类型构造扫描。
- **G3-04/G3-05 消费链收束（2026-09-06）**：`[F]` 上层虚表 `0x11b25144+0x14=0x107f67f0`；该 wrapper 取 `upper+0x1f41d4 → Campaign_ENV+0x28 → CampaignModel`，调用 `0x107f6540`，再经 `0x107f66b6` 调 `0x107f5580`，最后把 `pending+0x34==4` 的结果写入 `upper+0x1f41e0`。`0x107a7fb0` 是该状态字的读取器，索引中唯一直接 caller 是 `0x107f6540`；读取后仍进入 `0x107a69c0/0x107d8d70` 的 CampaignModel/PENDING_BATTLE 处理。`[F]` 原始 `.text` 直接 call 扫描确认状态链未调用 `0x102c8e30/0x102e5ec0/0x102e5fc0`；后者只作为 `0x11adfa40+0x28/+0x38` 的 BATTLE_ENV 工厂槽，当前没有从 ready 字或其读点接入的证据。`[U]` 因此 state 4 的消费链静态闭合到 upper 缓存和 pending 后处理，但没有闭合到 BATTLE_ENV、battle_mgr 或 spectator。
- **2026-09-06 实机强制加载成功（Goal3 R-1B 主路径打通）**：运行时 patch `0x10B9DA20` 返回 0（`30 C0 C3`，原字节 `56 8B F1`）→ AI-only pending 不再走 state 6 自动结算，而是进入 state 3/4 加载分支。实测：AI-only P=`0x27bec9c0`（vote_cnt=0）在 patch 后 `+0x38` 由 1 → 4；随后对象 vtable 切换/释放，Campaign Model vtable 让位，进程进入 AI-vs-AI 战场；用户确认能看到双方交战。证据目录 `testkit/results/20260906_233344_548_force_ai_load/` 与 `20260906_233518_500_goal3_success_evidence/`。
- **2026-09-07 精修静态定位**：①退出/ESC 链 = `BCQ_FACTION_QUIT_BATTLE handler 0x10446c00 → QUIT_SETTLE 0x1016e3b0 → BATTLE_END_RESULT 0x10167cb0 → RESULT_SUBMIT 0x10600de0`；错误归属 = `0x1016e3f6` 写 `[battle+0x23e0]`（本地无真人→侧 0=攻方→翻转→攻方败）。修复候选：Fix-3 官方 FORCE_BATTLE_END 旁路 / Fix-1 归属值覆写 / Fix-2 3K 式 arg8→builder A（现探针用 `0x1016e449: 00→01` 路由 builder A）。②规模筛选：AI-only P 的军队在 `P+0x48/P+0x4C`（攻/守 side），引擎聚合函数 `FUN_10BADB10` 可求规模；`P+0xA5` 是原生 AI 内战真打概率掷骰，非规模位；推荐条件桩替代恒返回 0。详见 `work/g3_attila_exit_fix_research.md`、`work/g3_attila_scale_filter_research.md`。
- **2026-09-07 战斗类型锁定已具备**：`P+0x40` 是 int 枚举 0..18（官方字符串表 `0x11cceef8`），ctor 写入先于挂载；官方 siege={6,9}，含据点={3..10}，野战={0..2}，海战={11..14,17,18}；`P+0x44 != 0` = has_contested_garrison，`P+0xAE` = ambush，`P+0xF8` = night。已实装到 `host_scale_filter.py` + GUI。详见 `work/g3_attila_battle_type_research.md`。
- **2026-09-07 defer v2（确定性 state-setter hook）**：hook `FUN_10B5F310`（状态 setter），当 armed P 正要写 state 5/9（自动结算链）时改写为 1，让状态机回 state1 再消费决策槽。不再用 watcher 外部回卷 `P+0x38`（有指针复用/终态风险）。GUI 启动自动修复残留 E9 钩子。
- **2026-09-07 单次加载后不再捕捉 → CM 重定位**：战斗加载后 Campaign Model 可能被重建/换址；GUI watcher 现在每轮校验 `CM vtable`，失效则堆扫重新定位 `CM`，回战役后可继续捕捉下一场。
- [x] 加载状态机入口 + 自动旁观判定（实机初验：AI 内战可看；完整结束/旁观身份字段仍待进一步确认）
- [x] fork/vote/ready 串族锚（`PRE_BATTLE_VOTING/FACTION_VOTE/READY_TO_FIGHT/CCQ_SET_PENDING_BATTLE_*` 全套原名内嵌）✅实验 001/003

## §1a 地址速查（✅实验 003 静态锁定，语义⬜待实机）

| 锚 | Attila VA | 备注 |
|---|---|---|
| `CCQ_SET_PENDING_BATTLE_READY_TO_START` handler | **0x10add490** | 注册函数 `0x10075970` 明确绑定；gate `cmd+4==0` → 解析参数(FUN_10aa9830, 0x81) → 查对象(FUN_102d4e60) → 副作用链 **0x107f1770→0x10bc0e10→0x10b87d20**。`10b87d20` 另有通用推进调用者 `10bcad80`，因此它是 pending-vote 状态机真身而非一次性桩。 |
| `CCQ_SET_PENDING_BATTLE_AUTORESOLVER_BATTLE_STANCE` handler | 0x10add390 | 自动结算立场 setter |
| `CCQ_FACTION_SWITCH_HUMAN_TO_AI` handler | 0x10ad96a0 | 目标2静态链已裁决：按 key 命中 `CAI_ACTIVE_FACTION` 后翻转 `+0x84c` 并懒建 AI 子系统；单人完整效果待实机 |
| CCQ 注册单例（mov ecx 全局） | 0x12262564 | 战役命令队列注册入口对象 |
| BCQ/BNCQ 共享注册函数 | 0x104b3ba0 | 哈希表插入（盐 0x4a545eed），运行时 hook 可 dump 全表 |
| `PENDING_BATTLE_SCRIPT_INTERFACE` Lua userdata ctor | 0x106fd140 | 官方 Lua 面 → pending battle 对象的引擎侧绑定 |
| 全命令表 | `re/attila_out/{ccq,bcq,bncq}_table.txt` | 402 条 100% 锁定 |

## §2 路线占位（分层沿用 s2 14 号图纪律）

- 路线1（注入/驱动机器）：找到分叉输入 → 外部写 or hook 返回值（3K 式）
- 路线2（仿照人类存在）：伪造参战方足迹
- 路线4（★实验 002 新增）：GFB `prevent_deployment`+无玩家军队（官方通道翻盘点，见 33 R-4）
- 钥匙进度：K1 pending 锚定 🟡（handler 锚✅，对象字段⬜）/ K2 状态机读法 ⬜ / K3 旁观判定 ⬜ / K4 观测通道 🟡（官方 Lua `cm:pending_battle()` ✅直出，控制台装设⬜）
