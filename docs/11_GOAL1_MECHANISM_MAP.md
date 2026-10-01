# 目标1 机制地图（11_GOAL1_MECHANISM_MAP）— 阿提拉：原生 AI 托管玩家部队

> 状态：**未开工**（仅登记跨项目起点，禁止当结论使用）。当前成立结论唯一载体 = 本文件；证伪/改写 → `12_GOAL1_LOGBOOK.md`。

## §0 跨项目认知源（机制概念，勿重新推导）

- 幕府2 已确证（s2 docs/11）：军队级字段 `a270=0（AI 激活前提）/a28c=1/a290=1.0f/a294=-1` + 单位级 `+0xea8=1/+0xc01=1` = 原生 AI 接管（身份替换，非脚本型）；`battle_ai` 挂钩点唯一 0x1adf50；a270=0 触发速度锁（引擎设计）。
- 官方脚本边界（3K/WH3 已确证，s2 docs/70 铁证）：官方 API 的「交 AI」= **脚本型 AI**（script_ai_planner/take_control），与原生 AI 是两种机制。
- 阿提拉官方先例（ENGINE_FAMILY_SURVEY §1）：AI General mod = 替换 `campaigns/*/scripting.lua`，Shift+F9 交全军 → **脚本型通道零成本可达**。

## §1 阿提拉待找对应物

- [ ] 军队对象「AI 控制权」字段族（s2 a270/a28c/a290/a294 等价物）——静态路径：`BNCQ_ARMY_ORDER_SWITCH_AI` 原型对象 `0x12168a44` 反查 ctor/序列化代码
- [ ] 单位对象 control 字段（s2 +0xea8/+0xc01 等价物）——锚 `BCQ_UNIT_CHANGE_CONTROL_STATUS`（下表）
- [x] BCQ 命令族锚（实验 001 串在 ✅ + **实验 003 全量地址锁定 ✅**：BCQ 204/204、BNCQ 1/1，共享注册函数 `0x104b3ba0`）
- [x] 原生 battle AI「决策入口」定位方法：Ghidra 索引已建成（84,724 函数；RTTI 类名可用，30 §3b）

## §1b 2026-09-06 BNCQ/BCQ 静态字段映射

- `BNCQ_ARMY_ORDER_SWITCH_AI` 注册于 `0x1004f560`，原型 cell `0x12168a44`，执行函数锁定为 `0x1044bd60`；`.bss` 原型 cell 是运行时命令描述槽，不是 handler/vtable。
- `0x1044bd60` 对军队候选对象写入：`+0x270=命令字节`、`+0x28c=1`、`+0x290=1.0f`、`+0x294=-1`；同时可能同步单位 `+0x1fd8=1`、`+0x1b60=1` 及子对象 `+0x1184/+0x117c=1`。字段语义和“原生 AI 接管”效果仍待实机。
- `BCQ_UNIT_CHANGE_CONTROL_STATUS` 注册于 `0x1004f0a0`，原型 cell `0x12169804`，执行函数 `0x1044aad0`；该函数直接写单位候选 `+0x1fd8`。类名未确证，不能把字段候选写成最终布局。

## §1a 地址速查（✅实验 003 静态锁定，语义⬜待实机）

| 锚 | Attila VA | 备注 |
|---|---|---|
| `BNCQ_ARMY_ORDER_SWITCH_AI` 注册点 | 0x1004f568 | s2 目标1 同名钥匙命令（3K 已无此名，s2↔Attila 独有配对） |
| ↳ 命令原型全局（.bss） | 0x12168a44 | 运行时 ctor 构造；静态读不到 handler，运行时 hook registrar 可 dump |
| BCQ 共享注册函数 | 0x104b3ba0 | 哈希表(盐 0x4a545eed)插入；**观测/枚举全表的理想 hook 点** |
| `BCQ_CREATE_AI_SCRIPT_CONTROLLER` | 注册 0x1004e108 / 原型 0x12166f04 | 脚本型 AI 控制器（对照组） |
| `BCQ_ADD/REMOVE_UNIT_TO_AI_SCRIPT_CONTROLLER` | 0x1004dc08 / 0x1004ea68 | 同上 |
| `BCQ_UNIT_CHANGE_CONTROL_STATUS` | 0x1004f0a8 / 原型 0x12169804 | 单位级控制权切换候选 |
| 全命令表 | `re/attila_out/{ccq,bcq,bncq}_table.txt` | 402 条 100% |

## §2 路线占位

- 路线A 官方 scripting.lua 脚本接管（质量=脚本型，非目标验收标准，可作观测通道）
- 路线B 引擎层字段直写（s2 同款方法论，目标达成线）
- 探索决策见 `13_GOAL1_EXPLORATION_MAP.md`
