# 目标2 机制地图（21_GOAL2_MECHANISM_MAP）— 阿提拉：玩家派系 CAI 自主发展（看海）

说明：文中出现的 work/ 、testkit/ 、experiments/ 、outputs/ 、research/ 、extract/ 、re/ 等路径指作者私有工作目录，未随本库公开。

> 状态：**实机闭环已达成（2026-09-07 东哥特 AI化成功）**。当前成立结论唯一载体 = 本文件；证伪 → `22_GOAL2_LOGBOOK.md`（已记 G2-L1..L16）。

## §0s 实机闭环（2026-09-07 定格）

- **运行时布局**：Campaign Model vtable `RVA 0x1B1FE54` 堆扫可定位；`CM+0x1c2c` = CAI 容器（count `+0x50`、array `+0x54`），`CM+0x1c44` = manager 表对象（vector `+0x590`/count `+0x58c`，条目 stride 8：`[manager对象, CAIMT类型]`）。
- **人控语义修正**：CAI 行 `+0x84c=1` + `+0x878/+0x874` 非空 = 人控/本地；AI 派系行 `0` 且空。
- **AI化操作**：选中 CAI 行 flag=1 → 找到 manager 表中 `CAIMT_HUMAN(6)` 条目 → 写 flag=0、manager type=0（FULL_MANAGER）、manager slots=0。用户实机确认失去手动控制并自动过回合。
- **恢复人控**：本会话 AI化 过的行 → 写 manager type=6、slots=6、flag=1。
- **工具**：`work/g2_scan_cai.py`、`work/g2_switch_to_ai.py`、`work/attila_control.{py,spec}`（dist 在 `work/dist/attila_control.exe`）。

## §0r 运行时现状（历史，2026-09-06）

- **闸门 ✅**：pid=24528 稳定，ASLR delta=+0x4a6f0000；run 10（10:54:51）**14/14 锚 check_window 算术自证 + scratch 全绿** → mutation 资格已解锁，只欠语义。⚠️ **24528 已于午后消失（无崩溃记录）；重开=新进程 40340 @ 0x5f700000（delta=+0x4F700000）——本节所有运行时地址（含旁探针 0x1b1f7f74、表候选 0x5c31e3a0）为旧 base 值，重扫前一律按静态口径重算；重开闸门 10 需再跑一次（check_window 与 base 无关，属例行动作）。**
- **根链现状**：`.bss` 全局 cell（CCQ 0x12262564 / BCQ proto 0xf3f63953）解引用=MEM_RESERVE 垃圾（G2-L2）→ 对象发现改**无根堆签名**。
- **24 表扫描（run 110136）**：24 张同质指针向量表全部镜像内真类；`+0x84c` 孤证=float 巧合（G2-L4）。**头号运行时表候选=0x5c31e3a0（cnt9，+0x84c 真 0/1 混合）**，但其 RVA/静态地址口径与类归属尚未裁决（G2-L6）。
- **manager 实例定位三条路（解封后按序）**：
  - **A（静态对拍，暂降级）**：先校准 `0x5c31e3a0` 的运行时地址与 DLL image base；当前 `RVA 0x31E3A0` 落在函数代码，未形成 vtable 归属证据，故转 S-02。
  - **A2（manager 根，当前优先）**：以 `0x10763710` 的 `CAMPAIGN_MODEL::CAMPAIGN_MODEL` 构造链为静态锚，确认其 `+0x1c2c/+0x1c38` 初始化与 `10b54580()` 返回值写入；运行时再验证该 Campaign Model 实例和 `+0x1c38` 对象。**活根取法（ctor 反汇编实锤，一条堆扫）：首条 `mov [ebx],0x11B1FE54` = Campaign Model vtable（RVA 0x1B1FE54）→ 堆扫 u32==模块基址+0x1B1FE54 即活实例；备选锚=命令 handler 运行时指针（静态 handler VA+delta 现于堆中=CCQ 原型活对象）。**
  - **B（借 Goal3 道）**：D1 弹窗 → FACTION_VOTE 记录 → 行内 faction/manager 指针链回摸（vote 系统与 pending/战役模型有引用关系）。
  - **C（被挡）**：C1b 远程调 handler 0x10ad96a0 需要 manager this——A/B 成则解套。
- **旁探针（白捡 ✅）**：`0x1b1f7f74` 四连块=[国库,62,收入,395]，三值链原地更新 → UI 活性/回合/收入观测用（**投影，非模型**，G2-L5）。
- 工具就绪：treasure_scan（数值反查 v2）/faction_table_scan（待加行大小估计）/faction_record_hunt（已封）；场景 46/47。

## §0 跨项目认知源（机制概念，勿重新推导）

- 幕府2 已确证闭环（s2 26_HANDOFF + 40）：`faction+0x6a0=0`（人类标志清除）+ manager 表置 `FULL_MANAGER` = 真看海（AI 玩到 34 回合，招募/进军，可存档）；恢复人控合法（manager→HUMAN + 0x6a0→1）。manager 表 key+0x164→faction 映射。
- 官方边界（**实验 002 grep 实证 ✅**）：Attila 官方脚本**无**「玩家派系切 CAI」通道（`switch_to_cai/handover/grant_faction/faction_manager` 0 hits，同 3K/WH3 结论）；且其脚本层比幕府2 **更强**（cm v1 世代=3K 框架祖先，非更弱——本行旧猜测已修正），观测（`is_human` 63 hits）可直读。
- startpos 通道（TWC CAI 权威帖，s2 时代知识）：manager 按派系写在 startpos.esf → Attila startpos（`campaigns/pro_attila/startpos.esf`，实测存在于 manifest）同样可编辑（EditSF/esfpy 支持 PFH4 时代 ESF ⬜待验证工具兼容）。
- 旁路候选：热座/多人掉线 AI 接管语义曾由 M2TW 先例提出；Attila 已完成静态存在性检查但未形成 CAI 链，现已关闭（G2-L6）。

## §1 阿提拉待找对应物

- [x] faction 对象「人类控制/CAI 启用」标志字段：`CAI_ACTIVE_FACTION` 对象 `+0x84c`（方法 `0x1072e330` 翻转；由 0→1 时创建 `+0x878`、`+0x874` 两个 AI 子系统）
- [x] CAI manager 类型枚举与表：`CAIMT_*` 10 hits + `FULL_MANAGER` 原名在 ✅（实验 001）
- [x] `CCQ_FACTION_SWITCH_HUMAN_TO_AI` → **handler=`0x10ad96a0`**（实验 003 续查）。原始汇编确认：解析一个 faction key → 遍历 `*(param_2+0x1c2c)` 的 `CAI_ACTIVE_FACTION` 指针表 → 以 `107239c0` 返回的 faction key 精确匹配 → `ECX=命中对象` 调 `1072e330`。后者翻转 `+0x84c`，由 0→1 时懒创建 `+0x878/+0x874` AI 子系统；最后 `107f1460` 按活跃 faction 数量重算全局标志 `param_1+0x1cc4`。**静态语义已裁决为 CAI 启用/停用开关（高置信度）**；仍待实机确认单人战役中的完整行为与可逆性。
- [ ] 「LocalFaction」注册点（静态未发现 CAI manager 注册证据；当前命中属于 `CAMPAIGN_ENV` 构造/加载与 Lua `campaign_manager.local_faction` 投影）
- [x] hotseat/多人掉线接管路径：**旁路关闭**。实验 001 的 HOTSEAT/IsLocalPlayerSpectating/local_faction 命中未形成接管链；多人 drop-in/spectate/player_disconnected 也未连到 `0x10ad96a0`、`0x1072e330` 或 `+0x84c`。

## §1b 2026-09-06 静态分工裁决

- S-01 的 `0x5c31e3a0` **暂不能归类为 manager 或 `CAI_ACTIVE_FACTION` vtable**。地址口径先行：按 image base `0x10000000`，RVA `0x31E3A0` 对应 `0x1031E3A0`，该处是函数代码而非 vtable；若 `0x5c31e3a0` 是运行时地址，则必须按当时模块基址重新反算，现有记录不足以直接拼接。候选静态位置未找到 ctor 写入、MSVC RTTI 或类归属证据。该线转 S-02，不在原地扩大扫描。
- 目标2当前最强静态主链仍是 `0x10ad96a0 → CAI_ACTIVE_FACTION(+0x84c) → 0x1072e330`。`0x10763710` 含 `CAMPAIGN_MODEL::CAMPAIGN_MODEL` 字符串和构造序列，按 `param_1[0x70b]`…`[0x70e]` 初始化 `+0x1c2c…+0x1c38`，并在 `param_1[0x70e]`（即 `+0x1c38`）写入 `FUN_10b54580(param_1+0x43c,1)` 返回值。进一步反汇编确认：调用前由 `0x100c92f0` 分配 `0x1b4`，`10b54580` 把 `this` 的 vtable 设为 `0x11b4b3b8`，并原样返回该 `this`；同族方法经 `0x10b697e0` 返回引擎类型名 `PENDING_BATTLE`，删除析构 `0x10b685c0` 也按 `0x1b4` 释放。因此 **`CampaignModel+0x1c38` 已静态锁为 `PENDING_BATTLE*`，不是上一级容器**；其 `+0xd4` 才是内嵌投票系统。
- `Campaign Model` 的持有链也已向上推进：`0x1075df80` 是 `CAMPAIGN_ENV::CAMPAIGN_ENV` 构造路径（`[this+4]=0x11b1e290`，函数末尾类型调试串确认），在 `0x1075efa0…0x1075eff3` 分配/加载 `0x1f78` Campaign Model 并保存到 `[Campaign_ENV+0x28]`。同一构造路径在条件分支 `0x1075f949…0x1075f97a` 分配 `0x1f41e4` 大对象、调用 `0x10766d70`，并保存到 `[Campaign_ENV+0x7c]`；后者构造时写入 vtable `0x11b25144`，再在 `0x10766dc9…0x10766e3f` 分配/构造 `Campaign_ENV` 并保存到 `[上层对象+0x1f41d4]`。对应析构 `0x10784c10/0x10792b00` 从 `+0x1f41d4` 释放 `0x118` 的 Campaign_ENV，再释放上层 `0x1f41e4` 对象，证明这是实际 wrapper↔env 生命周期链，不是单纯 getter。
- 独立消费者 `0x107f6802 → 0x107f6540` 从 `+0x1f41d4` 进入 `Campaign_ENV`，再读取 `env+0x28` 的模型 `+0x1c2c/+0x1c38`；因此当前静态结构是 **上层 wrapper(vtable `0x11b25144`，具体类名未解析) ↔ Campaign_ENV(+0x28=Campaign Model) → CampaignModel(+0x1c38=PENDING_BATTLE*)**。最终全局/注册表根、上层 wrapper 的外部保存槽，以及临时构造/长期加载两种入口的同一性，仍未锁。
- **2026-09-06 静态收口**：对 `0x11b25144` 的前 9 个虚函数做了原始汇编核对：`107b8c50/107b8970/107b8c40/107b8960/107f67f0/107b8c30/107b8950/107b8940` 均直接访问或转发 `this+0x1f41d4`；其中两个返回 `logs/mm_campaign_desync_{original,copy}.txt`，一个转入 `107f6540`。但 `vtable-4` (`0x11b25140`) 为 0，未见可用 MSVC COL；该表及其方法也未关联独立类型 getter/类名字符串。因此 **upper 的具体引擎类名静态不可命名**，只能锁定为带 `Campaign_ENV*` 子对象的上层生命周期包装体。
- 生命周期方向进一步纠正为嵌套链，而不是同一对象的回环：`外层 Campaign_ENV+0x7c → upper(vtable 0x11b25144, size 0x1f41e4)+0x1f41d4 → 内层 Campaign_ENV(size 0x118)+0x28 → Campaign Model`。`10782f30` 在外层 ENV 析构时通过 `env+0x7c` 调 upper 的虚析构；`10784c10/10792b00` 再释放 upper 内层 `Campaign_ENV` 与 upper 本体。
- 外部持有根的最后静态边界：`106feae0/106febf0/106fecb0/106fedd0` 返回的 `Campaign_ENV*` 在 `100cdb20/100ce740` 中进入局部或由 `100d25e0` 追加到调用方提供的向量；`100d02f0` 另经 `100cfba0()` 使用静态单例 `0x11d528e8` 保存一个独立的 `0x1d0` 对象，但没有把 upper/ENV 指针写入该单例。现有证据未发现 upper/ENV 的固定全局/注册表槽，因此最终外部根与 live attach/replace 时机正式保留为**静态未闭合，转运行时逐跳**。
- `FUN_109b50d0()` **不能直接称为 manager 根**：其本体只有 `return *(*(param_1)+0x28)`，是二级 accessor；`0x107f6540` 只是通过自身 `+0x28` 使用 manager-like 对象并进入 `0x107f5580`。它保留为运行时逐跳辅助，不再作为静态根。
- **G2-03 静态边界（2026-09-06）**：`0x10072e70`/`0x10b10980` 已锁定 CCQ handler `0x10ad96a0` 在 `entry+0x18`；但 `0x10afc600→0x10afc650` 实际调用的是 `entry+0x10` 的首 dword，未见 `entry+0x18` 读取或可证明转发。`0x11318b60` 的唯一 caller `0x1130fa20` 属于 vtable `0x11bceb20` 的大型 Campaign host（分配大小 `0xd2ac0`，根槽 `[0x11d51ef8+0x898]`），不是 `CAMPAIGN_MODEL`；wrapper 的 `this+0xd291c` 实际对应 host `+0xd2918`，尚不能解释为 Campaign Model/holder。该线转运行时 dispatcher 抓参与 callable 对象观测。
- `grant_faction_handover`、`set_cai_faction_manager`、`set_all_cai_faction_managers` 保留为官方/脚本候选，但不能等同于 LocalFaction 或 hotseat 接管。

## §2 路线占位

- R-A startpos 编辑 + 控制台命令组合（若 Attila 有 CAI 控制台命令）
- R-B 引擎字段直写（s2 看海同款两段式）
- R-D hotseat 旁路（已关闭，详见 §1b）
