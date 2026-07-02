# 设计稿：给 auftrag 加三个终端交互接缝

日期：2026-07-02
状态：已通过 brainstorming 逐项确认，待写实现计划（writing-plans）

## 背景

auftrag 现在是**纯对话**的引导式访谈：Phase 0 让长官一次性倒出任务，Phase 1 把倒出的话分进五个框（Intent / Target state / Boundaries / Escalation / Done-criteria），Phase 2 对薄/空的框一次一问地逼问，Phase 3 用长官原话拼出 brief，Phase 4 落 Todoist 并问"派发还是存档"。

五个框、go/no-go 闸门、落位提议、派发/存档这些结构，全程**只存在于文字里**——看不见、不可点。本设计把 Claude Code CLI 已内置的终端交互控件（`AskUserQuestion` 的单选/多选与 `preview`、可重绘的表格视图）接到这个流程的三个接缝上，提高直观性。

## 命门（贯穿一切的不变量）

> **交互控件只落在「决策 / 导航 / 确认」的接缝上，绝不落在「五个框的内容」上。**

auftrag 的头号红线是「问，不要替他写」——五个框里的字必须出自长官本人。因此：
- 进度表**只显示状态字形**，永不回显长官原话、永不把框内容摘进视图。
- Todoist 菜单**只碰元数据**（项目、优先级、时间），不碰 brief 本体。
- 派发预览**只回显"即将发出的东西"**，不生成任何 box 答案。

任何一处开始用菜单给某个 box 出候选答案，这个 skill 就当场犯了它自己最想防的错（替长官把话写了，长官顺手点头放行一个平庸版本）。这条不变量是三个功能能否安全落地的判据，也是给未来维护者的护栏。

## 功能一：五框三态进度（贯穿 Phase 1 → 3）

**渲染形态**：一行状态条，某个框的状态一发生变化就重画（每落一个答案、或一次重新归类时），**不是每轮都刷屏**。

```
● Intent   ◐ Target   ○ Boundaries   ○ Escalation   ○ Done
Go/no-go: ✖
```

**三态定义**（给字形一个明确来源，挂到 grill-heuristics）：
- `○` 空 —— 长官没碰过这个框。
- `◐` 薄 —— 碰了，但触发了 `grill-heuristics.md` 里"水答案的 tell"（如 Intent 只复述任务、Target 写成步骤、Boundaries 是偏好、Escalation 写"不确定就问我"）。
- `●` 实 —— 过了该框的逼问挑战。

**Go/no-go 字形**：照搬现有 go/no-go bar，不新增判据——`Intent + Escalation` 为实**且** `Done` 非空 → `✔ 可发`；否则 `✖`。

**硬护栏**：只显示状态字形。绝不回显长官原话，绝不把框内容摘进这一行。它是"视图"，不是第二个 ghost-writer。

**为什么是重绘的行内表、不是 statusLine/HUD**：statusLine 是全局常驻、跨 session 的配置；auftrag 是按次临时调用的 skill。所以进度必须是对话内每轮按需重绘的行，不是 HUD。

## 功能二：Todoist 落位确认（Phase 4 · Step 2）

先照旧读 `mcp__claude_ai_todoist__find-projects { limit: 50 }`。然后把现在那句"一行文字提议"换成一次 `AskUserQuestion`（打包最多 2 问）：

- **项目**（单选）：选项 = 从 brief 内容匹配度最高的 ≤3 个项目（最佳那个标「(推荐)」）＋ `Other`（工具自动提供，用于自由填其他项目 / inbox）。
- **优先级**（单选）：`p1` / `p2` / `p3` / `p4`——读 brief 里的紧急/工单信号，把推荐值排第一；无信号默认 `p4`。

**Due / deadline 不做菜单**：仅当 brief 暗示了时间，才追一行文字（`dueString` 软排期 / `deadlineDate` 硬约束），行为不变。

菜单的回答**即**长官的明确确认，据此 `add-tasks`。用户 Esc 取消 → 不创建。MCP 失败照旧「报错、不谎称成功、不在失败的写入上硬派 agent」。「推荐而非静默自动设」的原则不变——只是把那一行推荐变成了可点的菜单。

## 功能三：派发 / 存档 + 预览（Phase 4 · Step 3）

把现在那句纯文字"派发还是存档？"换成 `AskUserQuestion` **单选**（单选才支持 `preview`）：

- **「派发 now」**：`preview` = 即将发给 Agent 工具的**完整任务指令**——`dispatch.md` 里的 escalation 前缀段 ＋ 全文 brief markdown。让长官在拍板前看清"到底会发出去什么"。
- **「存档」**：`preview` = `/start-todo <task_url>`（原样可粘的续跑行）。

不额外加第三个选项，Esc = 取消，保持极简。选后行为完全照 `references/dispatch.md`：派发走 Agent 工具（默认 `general-purpose`，带 escalation 前缀）；存档则以 `/start-todo <url>` 那一行收尾。

## 不做（YAGNI ／ 守 skill 自己的红线）

- 不上 statusLine / HUD（全局常驻，不适合按次调用的 skill）。
- 不做 Phase 2.5 分诊控件（本轮明确不选）。
- 不拿 `ExitPlanMode` 冒充 brief 审批——那个 UI 是给当前 session 自己的 plan 用的，借它会真的切换会话模式，属于语义劫持。
- 不加新文件 / hook / 校验脚本。守住 v0 极简。

## 改动的文件

- `SKILL.md` —— 在「The flow」下加一个"进度视图"小节（三态定义＋重绘时机＋只显状态的硬护栏）；在 Phase 4 两步加指针。
- `references/dispatch.md` —— Step 2（Todoist 落位改成 `AskUserQuestion` 形态）、Step 3（派发/存档改成带 `preview` 的单选）。
- `references/grill-heuristics.md` —— 加一行，把"水答案的 tell → `◐`"挂钩，给三态一个定义来源。

三处都是对既有相位的"重述成控件形态"或"加一个只读视图"，不引入新机制，不破坏「问，不替他写」「Done-criteria 硬停」「最小化 boundaries」等既有红线。

## 验收标准（这套东西算成功的判据）

1. 逼问过程中，长官任一时刻都能一眼看到五个框各自 空/薄/实、以及 go/no-go 亮没亮——且这一行里**没有任何一个字**是长官原话或其转述。
2. Phase 4 落位是一个可点的项目/优先级菜单（推荐项置顶），不再是一行需要口头确认的文字。
3. Phase 4 派发/存档是一个单选，长官在选「派发」前能在 `preview` 里看到即将发给 agent 的完整指令，在选「存档」前能看到 `/start-todo` 续跑行。
4. 全流程无一处用菜单为五个框生成候选答案。
