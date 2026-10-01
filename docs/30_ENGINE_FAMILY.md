# 引擎血缘静态判定（30_ENGINE_FAMILY）— 阿提拉像幕府2还是像三国

说明：文中出现的 work/ 、testkit/ 、experiments/ 、outputs/ 、research/ 、extract/ 、re/ 等路径指作者私有工作目录，未随本库公开。

> 实验 001 产出（2026-09-03）。数据 = `../experiments/001_engine_lineage_static/outputs/`（scan_lineage.py 三方扫描）。
> 结论标注：✅=本机二进制实测（已确证）；📚=库内已确证记录；❓=推断；⬜=未核实。

## 0. TL;DR 判定

**阿提拉在「决定迁移成本的维度」上是幕府2 的同门师弟，不是三国那样换代的表亲：**

1. ✅ 进程/二进制形态：32 位 MSVC DLL `empire.retail.dll`（image_base 0x10000000）——与幕府2 **同名、同位数、同镜像基、同节表形态**；3K 是 64 位 255MB 单体 exe、非 MSVC 节形态，工具链全部重做的那一类。
2. ✅ 源树血统：pdb 路径暴露家谱——幕府2 `t:\branches\shogun2\curator\shogun2\binaries\empire.retail.pdb`；阿提拉 `s:\branches\attila\curator`**`rome2`**`\binaries\empire.retail.pdb`；3K `T:\branches\3k\curator\common\...`📚。同一 perforce 结构，阿提拉的 binaries 直接挂在 **rome2 树**下（阿提拉=Rome2 换皮扩展），引擎 pdb 名从 Empire 时代一路沿用。
3. ✅ 机制命令名族整体保留（§2 表）：幕府2 目标1/2/3 逆向出的关键命令名 **`BNCQ_ARMY_ORDER_SWITCH_AI`、`CCQ_FACTION_SWITCH_HUMAN_TO_AI`、`CCQ_SET_PENDING_BATTLE_READY_TO_START` 及 `CCQ_SET_PENDING_BATTLE_*` 族、`PENDING_BATTLE_PARTICIPANT` 族、`CAIMT_*`/`FULL_MANAGER`、`PRE_BATTLE_VOTING`/`FACTION_VOTE`** 在阿提拉二进制**原名命中**。
4. ❗但 id 交集统计显示阿提拉同时非常靠近 3K（§3 解释）：家族树是 `s2(WS2) → Rome2 → Attila(WS3 32位末代) → WH(64位) → 3K`，阿提拉是**中间节点**——内容 schema 层像 3K（同出 Rome2），深层机制枚举与二进制工具形态像幕府2。

**对本项目的操作性结论：按「幕府2 手册」打（32 位工具链直接平移），用「3K 方法」加速（其命令注册表静态枚举已被验证可行，且 3K 比幕府2 更近）。**

## 1. 二进制形态对比 ✅（PE 实测，outputs/*_pe.json）

| 项 | 幕府2 引擎 | **阿提拉引擎** | 3K |
|---|---|---|---|
| 模块 | `Empire.Retail.dll` 25.8MB | **`empire.retail.dll` 31.8MB** | `Three_Kingdoms.exe` 255MB（单体） |
| 位数 | x86-32 | **x86-32 (0x14C)** | x64 (0x8664) |
| image_base | 0x10000000 | **0x10000000** | 0x140000000 |
| 节表 | .text/.rdata/.data/_RDATA/.rsrc/.reloc（MSVC） | **同构 + .msvcjmc/.rodata** | .bss/.xcode/.link/.tls$（非典型，.xcode 187MB 代码段） |
| 启动器 | shogun2.exe（小 exe + 引擎 DLL） | **Attila.exe 598KB + 引擎 DLL** | 无（exe 即引擎） |
| 版本 | — | **ProductVersion 3.2.1.0 / FileVersion 1.6.0.0（停更→成果保值）** | v1.7.1（停更） |
| dll SHA256 | — | `981B162E…8E05AB7`（全值见 05_LOGBOOK，P-AT4 基线） | — |

阿提拉安装目录伴生 `libmfxsw32.dll`/`twitchsdk_32_release.dll`/`avcodec-53`（32 位时代）📚辅证；且直接背着 `local_en_shared_rome2.pack`（与 Rome2 共享资源包）✅。

**资源层**：pack 魔数 幕府2=**PFH3** / 阿提拉=**PFH4** / 3K=**PFH5** ✅——三代连续，阿提拉夹在中间但离幕府2 只差一档（RPFM 全支持✅；esfpy/EditSF 对 Attila ESF 的兼容性 ⬜待验，s2 replay 记录 ESF 魔数 caab 族系📚）。

## 2. 机制命令字符串族三方计数 ✅（子串命中次数，outputs/*_markers.json）

| 标记 | 幕府2 | **阿提拉** | 3K | 含义 |
|---|---|---|---|---|
| `BCQ_` / `CCQ_` / `BNCQ_` | 193/173/1 | **204/199/1** | 182/191/1 | 战斗/战役命令队列注册表（唯一名 token 数 s2=193/172，Attila=204/199） |
| `CAI_` / `CAIMT_` / `FULL_MANAGER` | 693/11/3 | **505/10/3** | 712/10/2 | 战役 AI 与 manager 类型枚举 |
| `PENDING_BATTLE` / `PendingBattle` | 9/2 | **22/2** | 29/4 | pending battle 对象族 |
| `PRE_BATTLE_VOTING` / `FACTION_VOTE` / `READY_TO_FIGHT` | 2/1/1 | **2/1/1** | 3/1/1 | 开战前投票/就绪分叉族（b9 概念锚） |
| `autoresolve` | 101 | **85** | 125 | 自动结算族 |
| `unit_controller` / `take_control` / `release_control` | 3/1/1 | **3/1/1** | 3/1/1 | 单位控制器原语 |
| `battle_ai`+`BATTLE_AI` | 6 | **5** | **51** | 3K 战斗 AI 字符串面爆炸（新框架）；s2/Attila 同代紧凑 |
| `Lua 5.1` | 2 | **2** | 2 | 三代同嵌 Lua 5.1 时代 |
| `Warscape`+`warscape` | 72 | **94** | 158 | 引擎自称 |
| `IsLocalPlayerSpectating`/`hotseat`/`get_modify_pending_battle` | 0/0/0 | **0/0/0** | 1/1/1 | 这三个是 **3K 新增面**，Attila 没有——Attila 不站在 3K 那侧的反证 |

**原名命中的机制锚清单（Attila ✅，对照幕府2 记录 📚）**：
`BNCQ_ARMY_ORDER_SWITCH_AI`（s2 目标1 BCQ handler@0x2abeb0 同名命令✅；**3K 中不存在此名**→ s2↔Attila 独有配对）｜`CCQ_FACTION_SWITCH_HUMAN_TO_AI`（s2/3K/Attila 三家同在✅）｜`CCQ_SET_PENDING_BATTLE_READY_TO_START`（三家✅）｜`CCQ_SET_PENDING_BATTLE_{AUTORESOLVER_BATTLE_STANCE, FACTION_CAPTIVES_OPTION, OCCUPATION_DECISION, SETUP_DISCONNECTION_RESET, SETUP_INFO_SYNCHRONISED, WALL_MOUNTED_ARTILLERY_OPTION}`（Attila 全套✅）｜`BCQ_{CREATE,DESTROY}_AI_SCRIPT_CONTROLLER` + `BCQ_{ADD,REMOVE}_UNIT_TO_AI_SCRIPT_CONTROLLER` + `BCQ_AI_SCRIPT_CONTROLLER_SET_OBJECTIVE_*`（✅）｜`PENDING_BATTLE_{PARTICIPANT, FACTION, ALLIANCE, EVENT, SCRIPT_INTERFACE, PLAYER_READY_TO_SAVE_GAME}`（✅）。
清单全量见 `outputs/attila_inventory.txt`（BCQ_ 204 条/CCQ_ 199 条/token 级去重）。

⚠️ 教训平移（s2 24_HANDOFF 📚）：**命令名相同 ≠ 语义相同**（s2 的 `CCQ_FACTION_SWITCH_HUMAN_TO_AI` 实为 MP 掉线 pending battle 命令，非派系托管）。静态锁定 = 锁住锚点，语义必须实机裁决。

## 3. snake-id 交集统计 ✅（长度≥8 下划线标识符集合）

| 指标 | 值 |
|---|---|
| \|attila\| / \|s2\| / \|3k\| | 25,274 / 22,981 / 33,198 |
| attila∩s2 | 8,734（占 attila 34.6%） |
| attila∩3k | 12,352（占 attila 48.9%） |
| s2∩3k | 5,143（占 s2 22.4%） |
| 三者共 | 4,946 ｜ 仅 attila | 9,134 |
| attila∩s2 非 3k | 3,788 ｜ attila∩3k 非 s2 | 7,406 |

解读（❓推断，样例支撑 ✅）：字面比例上 attila 更近 3K——差集内容揭示原因：**attila∩3k非s2** 主要是 Rome2 世代引入的内容/系统 schema（`ACTION_LOG_*`、`ACHIEVEMENT_*`、`AIH_*` 战场提示类型、`ADD_PROVINCE_DEVELOPMENT_POINT`…）——Attila 与 3K 共享 Rome2 后代 schema；**attila∩s2非3k** 则集中在深层机制枚举（`AI_TACTIC_OUTFLANK/DOUBLE_ENVELOPMENT/REPAIR_NAVAL`、`AI_FORCE_{ATTACK,DEFENCE,WITHDRAW}_PLAN`、`AGENT_INDICATOR_*`、`ARMY_REINFORCEMENT_MANAGER`、`ANCILLARY_*`——3K 已改名/删除的辅助系统）。**族谱定位：Attila 是 s2 与 3K 之间的桥**；对本项目的逆向迁移而言，锚点三家里 Attila 与 s2 语义配对最完整（§2 表末行反证）。

## 3a. 脚本层世代判定（实验 002，✅grep 实证）

**嵌合体定位：二进制层像幕府2，脚本层像三国。** 阿提拉自带 `script/_lib` 26 库（`lib_script_ai_planner`/`lib_generated_battle`/`lib_battlemanager`…）+ `cm:` 上下文 98 hits；`query_model` 0、s2 式 `monitor` 0 → Attila = **cm v1 世代**，正是 3K/WH3 脚本框架（cm v2）的祖先代。含义：3K 项目验证过的官方脚本观测手段在阿提拉有现成等价（甚至更宽，`cm:pending_battle()` 全家桶 422 hits）；幕府2 的 monitor 时代脚本经验在此不适用。详见 `../experiments/002_official_lua_surface/README.md`。

## 3b. RTTI 命名空间级配对（Ghidra 分析日志，✅2026-09-03 运行轮）

Attila 二进制保留**完全限定 MSVC RTTI 类名**：`EMPIRECAMPAIGN::MILITARY_FORCE`、`EMPIRECAMPAIGNAI::MILITARY_GENERATOR_ARMY_TEMPLATE`、`EMPIRECAMPAIGNAI::TMS::TMS_COORDINATOR_INTERNAL::TMS_OWN_ARMY`、`EMPIREUTILITY::CAMPAIGN_MAP_ATTRITION_RECORD`、`EMPIRECAMPAIGN::CAMPAIGN_VICTORY_CONDITION_TYPE`…；幕府2 Ghidra 导出（strings.json 📚）同样含 `EMPIRECAMPAIGNAI::DIPLOMATIC_ACTION` / `EMPIRECAMPAIGNAI::NEGOTIATION` 与 **`UTILITYDLL::LUA::State::operator<>` 自研 Lua 绑定器**——两家共用 `EMPIRE*`/`UTILITYDLL` 命名空间体系 = **符号级同源**（比族谱推断更硬的证据）。
**静态锁定含义（升级）**：除字符串锚外，Attila 可走 **RTTI 类名恢复**（Ghidra MicrosoftCodeAnalyzer + `RecoverClassesFromRTTIScript`，s2 专用 harness `run_shogun2_msvc_x86.ps1` 已有两种模式可仿）→ 目标类（MILITARY_FORCE/FACTION/PENDING_BATTLE 族）**按名直指**，成本低于 3K 纯启发式。s2 时代 ClassRecovery 曾在 25MB DLL 上跑 16min 未完（实验 005 📚），Attila 31.8MB 预留后台轮。

## 4. 位数矛盾裁决（P-AT1 闭环）

- 根库 `s2/research/ENGINE_FAMILY_SURVEY.md`：Attila=32 位 ✅ **维持**（本项目实测）。
- `tw3k_ai_battle/docs/30_ENGINE_FAMILY.md`：把 Rome2/Attila 划入「64 位分支」❌ **对本机零售版证伪**（其「Rome2 系=64 位」表述过宽：正确表述=WH1 起 64 位，Rome2/Attila 仍 32 位）。已登记本库 04_PROBLEMS P-AT1；tw3k 原文不改（历史文档）。

## 5. 对三目标迁移的含义（操作表）

| 维度 | 迁移源 | 依据 |
|---|---|---|
| 注入/直写工具链（CreateRemoteThread、提权启动器、Toolhelp32、s2_control 类 GUI 骨架） | **幕府2 直接平移**（32 位同形态） | §1 ✅ |
| 静态枚举方法（命令注册表 `lea/push name + lea/push handler + call registrar` 模式） | **3K 方法平移**（tw3k 00_INDEX 已验证 x64 版；x86 版更简单）❓模式待 Ghidra 确认 | §2 ✅ + 3K 📚 |
| b9 思路（分叉输入/人类加载链/自动旁观） | 概念从幕府2，锚点查找法从 3K（fork6o = 强制谓词返回值） | s2 40 📚 / 3K 31§2.21 📚 |
| CAIMT manager/faction 人类标志定位（目标2） | 幕府2 概念（+0x6a0/manager 表两段式）+ Attila startpos.esf 差分辅助 | §2 串族 ✅ |
| 官方脚本层（目标1 脚本接管/观测通道） | **Attila 自家最强**（Lua 5.1 嵌入 ✅ + Assembly Kit + ConsulScriptum/TWASE 先例 📚） | ENGINE_FAMILY_SURVEY §3 📚 |

## 6. 待办验证清单

- [ ] Ghidra x86 headless（re_toolkit `--project attila`，配置已注册）→ 验证命令注册表模式 + 导出函数/字符串索引
- [ ] data.pack 提取 lua/脚本 → grep Attila 官方脚本面（目标2/3 API 存在性，仿 tw3k grep 方法论）
- [ ] esfpy 解 Attila startpos/存档 → `PENDING_BATTLE` 树 + 人类/AI 派系字段差分（b9 概念搜索）
- [ ] 幕府2 函数级字节签名 → Attila 静态扫描命中率实验（A1 线）
- [ ] 实机基线（P-AT3）
