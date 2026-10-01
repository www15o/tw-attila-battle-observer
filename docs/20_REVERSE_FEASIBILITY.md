# 逆向可行性 / 静态锁定评估（20_REVERSE_FEASIBILITY）— 阿提拉

说明：文中出现的 work/ 、testkit/ 、experiments/ 、outputs/ 、research/ 、extract/ 、re/ 等路径指作者私有工作目录，未随本库公开。

> 核心问题：**阿提拉能不能靠静态直接锁定好？**（vs 幕府2 当年数月实机 hook 摸索 / 3K 的静态注册表枚举成功）
> 依据：实验 001 静态扫描（30_ENGINE_FAMILY 数据）+ 跨项目已确证记录。置信度标注同 30。

## 0. 三项目基准

| | 幕府2（基准） | 3K（对照） | **阿提拉（本项目）** |
|---|---|---|---|
| 形态 | 32 位引擎 DLL | 64 位单体 exe | **32 位引擎 DLL（同幕府2）** ✅ |
| 关键逻辑点获取成本 | **数月**：hook/差分/实机反推（状态机、+0x6a0、b9 全 runtime 破案） | **低-中**：字符串锚→静态枚举 191 CCQ+129 BCQ 全表带 handler 📚 | **预期 = 3K 同款静态可枚举** ❓（前提 §1 已具备） |
| 注入工具链 | 自建 32 位（s2_ai_ctl/s2_control/_run_elev） | 64 位重做 | **幕府2 套件直接复用** ✅（位数/调用约定/镜像基同） |
| 成果保值 | 停更 ✅ | 停更 v1.7.1 ✅ | **停更 3.2.1** ✅ |

## 1. 静态可锁定性证据链 ✅

1. **锚点层**：三目标全部机制命令名在 Attila 二进制原名存在（30 §2 清单，含 s2↔Attila 独有的 `BNCQ_ARMY_ORDER_SWITCH_AI`）。CA 引擎把命令名以明文内嵌 → 名字→注册表→handler 的静态反查路线**材料齐备**。
2. **方法层**：3K 在同一字符串族上完成全静态枚举（regblock 模式识别 + 命令表 dump，tw3k work/3k_regblocks_all.py 📚）。Attila = x86-32/MSVC：注册块预期为 `push imm32; call registrar` 或 `.rdata` 静态表，**比 3K 的 lea 模式更简单**。❓具体模式 Ghidra 一轮即可定。
3. **对象层**：pending battle/manager/单位控制器的**字段偏移**无法只靠字符串锁定（无符号）→ 需 Ghidra 反编译 +（存档 ESF 差分/实机校准）。这是幕府2 与 3K 都躲不掉的一段。
4. **pdb/RTTI 红利**：Attila 保留源树 pdb 路径 ✅；32 位 MSVC RTTI 在 s2 实验 005 已被证明可部分恢复类名（📚 已跑 16min 中止，无最终计数）——Attila 同法可试，若 RTTI 完整则**静态锁定成本再降一档**（类名直接锚定）。

## 2. 分层结论（对齐通道优先级）

| 层 | 结论 | 置信 |
|---|---|---|
| 数据/资源层（RPFM·PFH4、EditSF/esfpy·ESF、Lua 脚本明文在 pack） | 工具全部现成，零逆向 | ✅ |
| 观测层（游戏内状态查询） | ✅ **官方 Lua 直出（实验 002 实证）**：`cm:pending_battle()` 访问器全家桶（attacker/defender/has_attacker/night_battle/percentage_*/result 422 hits）+ `pending_battle_cache_*` + camera 173 hits + CA 自带 UI 自动化 harness（autorun.lua：SimulateClick/SimulateKey/Timers/PanelOpened）——幕府2 当年 hook 数月拿到的东西这里一行脚本 | ✅ |
| 目标1 脚本型接管 | 官方 scripting.lua 现成先例（AI General mod 📚） | ✅存在（质量=脚本型，非验收） |
| 目标1/2/3 **达成层** | 无官方通道的部分（原生 AI 质量/派系托管/强制加载 AI 战斗）→ 引擎层；**32 位可全程用幕府2 已验证工具形态** | ❓ |
| b9 等价物 | 分叉输入族串锚在（PRE_BATTLE_VOTING/READY_TO_FIGHT/CCQ_SET_PENDING_BATTLE_* ✅）；3K 版「强制谓词返回值」路线（fork6o 📚）预期同样适用 | ❓ |

## 3. 与幕府2 时代的成本对比（预测，供复盘校准）

- 幕府2 达成目标3 用了 ≈ 数周实机+百级 hook 记录 📚；**Attila 预测**：Ghidra 建索引（1 轮）→ 注册表静态枚举（1-2 轮）→ pending/manager 对象字段定位（数轮）→ 实机验证。字符串锚点密度高于 3K 场景里没有的优势：**幕府2 的字段语义地图可当「已标注的族谱参照」**（同代结构，字段族排布大概率相似——❓不可直接搬偏移）。
- 风险：3.2.1 版本较旧，若日后升级 Steam 版可能漂移（记录 SHA256 基线对冲）；官方 Lua 面若比预期强，可能直接吃掉部分达成层（好事，按根 §0 立即弃逆向）。

## 4. 下一步行动（P0/P1）

1. **P0**~~re_toolkit 跑 headless~~ **进行中（pwsh-5）**：import+analysis 完成 → ExportIndex → build_index → 检索通道就绪
2. **P0**~~RPFM 解包 grep 官方 API 面~~ **✅完成（实验 002）**：边界矩阵落档；GFB 翻盘候选入 33 R-4
3. **P1** attila_regblocks.py（移植 3K 模式，x86 版）→ 命令注册表全量 dump（名→handler 地址）
4. **P1** esfpy 解 startpos.esf + 人工/AI 两态存档差分 → faction 对象候选字段表
5. **P1** 实机基线（P-AT3）：启动→打一仗→截图/日志/存档快照
