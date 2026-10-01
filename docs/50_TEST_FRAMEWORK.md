# 50_TEST_FRAMEWORK — 阿提拉实机测试框架（testkit）

说明：文中出现的 work/ 、testkit/ 、experiments/ 、outputs/ 、research/ 、extract/ 、re/ 等路径指作者私有工作目录，未随本库公开。

> 定位：目标1/2/3 的**补充测试统一引擎**——把「实机随时可测」工程化：环境就绪检查、观测通道校准、只读探针、写实验门禁、证据落盘。代码在 `../testkit/`，本文档是唯一说明书（开工读本文 + 00_INDEX + §9 开工卡）。

## 1. 架构（三通道 × 四层门）

```
通道A 进程内存（pb.py：RPM/WPM/scratch/reloc/区域走查，自 s2 probe_battle_env 平移）
通道B 证据采集（shots.py：截图/日志/文件快照）
通道C 场景引擎（framework.py：YAML 步骤 = preflight|observe|calibrate|mutate|capture|note）

L0 静态基线（不需游戏）→ L1 attach+校准 → L2 只读探针（分目标）→ L3 写实验（门禁）
```

**硬纪律（根 AGENTS §3 的代码化）**：
- `mutate` 步骤**默认拒绝**，必须 `--allow-mutate` 显式开闸；
- 每次 `mutate` 账本**先落盘**再写（`rollback.json`，state 机 pre-write→verified/mismatch-restored），读回不符尽力还原；
- `calibrate` 是 mutate 前置资格赛：①scratch 写读回（自有内存=无害已知改动）②**逐锚点 `check_window` 算术自证**（窗口内 4 字节读数若为镜像内地址 → 内存值必=文件值+delta；DIFF 必被合法字段覆盖，其余严格相等）——任一失败=通道不可信，禁入修改。**2026-09-06 实证：reloc 表折算不可用（CA 私有重定位：未对齐 imm32 被修复但不在 .reloc 表）**。版本漂移防线在 preflight 的 SHA256 硬闸（不匹配当场 raise）。

## 2. 资产清单

| 文件 | 作用 |
|---|---|
| `anchors.json` | 24 锚点登记表（三目标钥匙级；402 命令全量表在 experiments/003 outputs）；含 `sizeof_image`/基线 hash；14 条 code 锚带 AOB `sig`（emit_sig 生成；**静态侧**唯一性资产，内存侧校准已不依赖它） |
| `pb.py` | find_pid(Toolhelp，HANDLE 全声明)/module_base/rpm/uXX/wpm(VP 成功后才还原)/scratch_calib/sig_scan(通配安全)/parse_relocs/reloc_adjusted_expect/iter_regions(堆走查) |
| `emit_sig.py` | AOB 生成器（只掩 rel32；site 锚原始切片；原子写回）——dll 更新后重锚用 |
| `framework.py` | 场景引擎 + `rebase()`(ASLR) + `image_mem()`(分块缓存) + `relocs()` + `alloc_scratch()` + 报告落盘 |
| `probes/` | `manager_hunt`/`faction_table_scan`/`faction_record_hunt`（目标2：堆签名与数值反查）；`votecore.py`+`vote_scan.py`（目标3：numpy 向量化 FACTION_VOTE 堆扫描）；`treasure_scan.py`（CE 式数值反查，u32/f32/f64+区间）；`pending_watch.py`（常驻差分吃帧 watcher） |
| `scenarios/` | 10 场景（§3） |
| `results/<run_id>/` | 一次 run 一目录（毫秒 id）：report.md + steps.jsonl + evidence/ + rollback.json（不入库） |

## 3. 场景矩阵

| 场景 | 需要 | 内容 | 判定意义 |
|---|---|---|---|
| `00_preflight` | 无 | dll SHA256 硬闸/进程探测/文件快照/日志目录/截图可用（游戏在跑则附基址+写通道探测） | 环境总闸 |
| `10_attach_calibrate` | 游戏运行 | 1KB .text check_window 完整性+BNCQ 串直读/**算术自证校准 v3**+scratch+基线证据 | **资格赛**（不绿禁 mutate；✅0906 10:54 全绿） |
| `20_g1_battle_probe` | +战斗中 | BCQ 原型全局运行时值→vtable 校验/关键函数入口 check_window/战斗日志采样 | 目标1 实机首裁 |
| `25_manager_walk` | 战役运行 | faction_table_scan（无根全堆签名扫：同质指针向量表 + 行 vtable 健康度 + 字段画像）| 目标2 地基（A2；**24 表已扫出，manager 未锁→暂封**） |
| `30_g2_campaign_probe` | 战役运行 | CCQ 单例链走+`+0x1c2c` 表探索性读数（被 25 取代大半，保留交叉） | 目标2 数据视角 |
| `40_g3_pending_vote_probe` | **pending 弹窗开着** | **同帧全家桶**：截图(地面真值)→vote 全量扫描→manager 同帧→入口 check_window→日志→汇总判定 | 目标3 D1 定位法 ★ |
| `45_watch_pending` | 游戏运行 | watcher 常驻循环（vars: watch_s/tick_bytes/tick_gap），状态差分自动落帧 | 目标3 D2（AI-AI 短窗口） |
| `46_treasure_hunt` | 游戏运行 | CE 式数值反查：u32/f32/f64 三型并行+区间+滚动候选 diff（vars: value/mode/diff/profile） | 数值锚（判决已收官：投影） |
| `47_faction_records` | 游戏运行 | 同胞记录布局全堆扫+stride 统计+持有者反查 | 目标2 布局判据（已封：宽松指纹=噪声） |
| `90_mutate_scaffold` | +`--allow-mutate` | preflight→calibrate→scratch 流水线演练（分配→写→账本→读回→回滚→释放）；M-G1/2/3 计划以 note 登记 | L3 全链预演 |

## 4. 用法速查

```powershell
cd <本仓库根目录>
python testkit\framework.py list
python testkit\framework.py run testkit\scenarios\00_preflight.yaml
python testkit\framework.py run testkit\scenarios\10_attach_calibrate.yaml
python testkit\framework.py run testkit\scenarios\25_manager_walk.yaml
python testkit\framework.py run testkit\scenarios\45_watch_pending.yaml --set watch_s=300
python testkit\framework.py run testkit\scenarios\90_mutate_scaffold.yaml --allow-mutate
python testkit\emit_sig.py            # dll 更新后：重锚+sig 再生（BAD≠0 停）
```

⚠️ 游戏若提权启动，需管理员身份跑 python（OpenProcess 写权限失败会明示 err）。

## 5. 已知边界与诚实登记（⬜）

- **官方 Lua 通道已砍**（用户决定 2026-09-06：现有资料中该通道信息缺口最大/不确定性高，不入关键路径）。观测=内存+截图+日志；GFB R-4 降为双败后重议备选。
- `param_2↔CCQ 单例` 同一性未证 → 由 `manager_hunt` 运行时反推代替（特征命中≠语义确证，产物标「候选」，终裁=行为归属）。
- 玩家派系行识别=「+0x84c==0」启发 ∩ key↔派系 index（startpos ESF 旁查未做，⬜）→ 终裁留给 C1 行为归属。
- AI-AI pending 窗口极短（CAI 秒结算）→ 依赖 45 watcher 自动吃帧；未实测扫到真实记录前的所有「hits=0」不构成证伪（预算/时机均可调）。
- 堆扫描指针界假定为 32 位用户空间 `<0x80000000`（若游戏带 LAA 高位堆分配需放宽，见 pb.iter_regions hi 参）。

## 6. 与三目标机制地图的挂点

- 目标1（11/13）：`20_g1` vtable 展开 → 11 §1a「运行时列」；SWITCH_AI 命令对象布局 dump 前置 M-G1。
- 目标2（21/23）：`25` 的 manager/表画像/zero-flag 行集 → 21 运行时列 + 玩家行候选集登记；C1 归属终裁进 22。
- 目标3（31/33）：`40/45` 的 this/vote 记录 → 31 §1 字段语义实机裁决；(+0x10/+0x11) 字节对操作 = M-G3 → 33 路线状态刷新。
- 每次 run 的 `report.md` 路径**必须**写进 05_LOGBOOK 对应条目（证据可回溯）。

## 7. 独立审查记录（2026-09-05，子代理只读审查）

**判定：需修复后使用 → 已全部处置，复跑回归通过。** 发现 P0×1 / P1×3 / P2×14。

### §7a 处置表

| # | 级别 | 问题 | 处置 |
|---|---|---|---|
| 1 | **P0** | `attach()` 缓存只读句柄后忽略 `need_write` 升级 → 实机场景必死在 calibrate（err=6）；`_probe_write` 另开句柄误导诊断 | ✅ 句柄权限位 `_writable`+升级重开；preflight 写探测统一路径 |
| 2 | P1 | mutate 读回不符宣称回滚实际不回滚、账本只成功后落盘 | ✅ 账本**写前落盘**（state 机），不符尽力还原并记录 |
| 3 | P1 | preflight hash 漂移只记不判；90 无版本门 | ✅ 漂移当场 raise；90 补 calibrate 门 |
| 4 | P1 | Toolhelp 三连未声明 restype/argtypes（HANDLE 截断潜伏坑） | ✅ 显式声明，find_pid 自测过 |
| 5-18 | P2 | 首字节通配漏配/空 pattern/VP 误还原/MISS 区分/`exp in hit`/模板 StopIteration/abort 死代码/capture 静默/run_id 秒级/重复读 DLL/文档陈旧/非原子写/0x1F00000/shots 小项 | ✅ 全修（SizeOfImage 入 meta；run_id 毫秒） |

**审查实证背书**：14/14 AOB 静态唯一命中且位置语义正确（site 锚=va−5）；缺省无 `--allow-mutate` 时无任何路径可写游戏真实内存；无循环导入。
**遗留登记（设计边界）**：observe=inline 任意 python，门禁防误操作不防蓄意（YAML 作者=完全权限，已写入框架 docstring）；30 号主菜单误 FAIL 属「记录不判定」用法。

## 8. 实机首照与校准 v2（2026-09-06 深夜，只读侦察）

**实机事实（✅实测，零写入）**：游戏启动成功；`empire.retail.dll @ 0x5a6f0000`——**ASLR 开启**（delta=+0x4a6f0000）；锚点字节 base+RVA 处 4/4 MATCH；串锚命中；**CCQ 单例实例=0x29f0edb8（战役图已构造，H-A2 运行时首裁）**；save_games=0；日志目录实为 `...\Attila\logs`。

**由此推翻并重建**：
1. 「保 imm32+基址=默认」的 AOB 内存校准被证伪（374,613 个 type-3 槽被 loader 全部 fixup）→ `op_calibrate` v2=reloc 折算逐字节验证；漂移防线前移至 SHA256 硬闸。真实槽位 0x1008d00c 折算回归 ✅。
2. AOB 仅存 emit_sig 静态侧作跨构建资产。
3. 新增堆观测基建：votecore/vote_scan/manager_hunt/pending_watch（§2）。
4. 场景 25/45 新增、40 重写同帧全家桶、10 完整性改 1KB reloc 比对。
5. 官方 Lua 通道砍除（§5）。

## 8a. 白天闸门战（2026-09-06 10:39–11:35）

1. **run 10 首红→v3 全绿**：reloc 折算被实证不可行——`empire.retail.dll` 有未对齐 imm32 被私有机制 +delta 修复，`.reloc` 表（仅 type0/3，4 对齐）不覆盖 → `op_calibrate` v3=**check_window 算术自证**（in-image 读数必=file+delta；DIFF 须被合法字段覆盖）→ **14/14+scratch 全绿，mutation 闸门解锁**（run 105451_608）。
2. `.bss` 全局 cell 判死刑（CCQ/BCQ proto 解引用=MEM_RESERVE）；对象发现=无根堆签名。
3. 新探针/场景：`treasure_scan`（46，数值反查 u32/f32/f64+区间+滚动候选，1.3GB/3.3s）、`faction_record_hunt`（47，同胞布局）、`faction_table_scan`（25，24 表画像）；数值锚判决=投影（同胞全堆唯一命中），Goal2 地基暂封于 21 §0r。

## 9. 白天开工卡（按序，勿跳）

```
（若游戏已关：启动并进战役）
A0  用户 GUI：另存 tk_base ＋ 关自动存档 ＋ 战斗设「手动」           ← D/E 前提  ✅10:41 已存
1   python testkit\framework.py run testkit\scenarios\00_preflight.yaml                       ← ✅PASS
2   python testkit\framework.py run testkit\scenarios\10_attach_calibrate.yaml   ← 绿=闸门（P0句柄+check_window v3 双首验） ✅10:54 全绿
3   ~~25 manager 猎取~~ → Goal2 暂封（21 §0r 三路待走）；~~46/47 数值反查~~ → 判决=投影，已封
4   load tk_base → 攻击 AI 部队（弹窗出现别点）→
    python testkit\framework.py run testkit\scenarios\40_g3_pending_vote_probe.yaml  ← 同帧全家桶 ★当前卡位
5   Goal3 推进：E1（玩家弹窗翻 ready/human）→ D2/45 watcher 采 AI-AI → E2（注入旁观 🎯目标3）
6   Goal2 解封：A 路静态对拍（vt RVA 0x31E3A0）或 B 路借 D1 vote 链 → C1 托管（🎯目标2）
```

⚠️ 纪律重申：10 不绿禁一切 mutate；实验期不手动保存；一次一变量；每步 report 路径回填 05。
