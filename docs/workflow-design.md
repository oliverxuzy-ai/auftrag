# Auftrag 的下半场：围绕 Claude Code 的完整 agentic workflow 设计

> 日期：2026-07-03 · 状态：设计稿，未实施
> 输入：你的四层痛点自述 + auftrag 仓库现状 + 三路调研（社区生态 / X 实践者一手经验 / Anthropic 官方能力清单，Claude Code v2.1.201）
> 本文档先检验你的痛点框架本身，再给设计。所有关键论断附来源。

---

## 0. TL;DR

你已经建好了流水线的**上半场**（auftrag = 派活时刻的契约质量），缺的是**下半场**（派出去之后的世界）。设计的核心动作只有一个：

**把你的管理对象从"N 个交互式 session"换成"一条带状态机的流水线 + 一个例外队列"。**

你只在三个位置出现：填契约（已有 /auftrag）、答升级（决策队列）、验收（分层抽查）。其余一切——执行、验证、状态汇报、举手——由机器完成。而且调研确认：这条流水线所需的基础设施（舰队面板、后台会话、完成/求助推送、Stop 门禁钩子）Anthropic 在 v2.1.139–2.1.201 之间已经原生发货了，你要建的只是把它们接到"任务语义状态"上的薄胶水层，大约三个小组件 + 两个 hook 脚本。

---

## 1. 先检验你的痛点框架（你要求不默认你是对的）

### 1.1 "两个病"的区分：方向对，但有一个关键错误

你说：*"病2 是输出可不可信的问题，我写再好的 brief 也解决不了。"*

**这句话过强，而且它正在误导你的设计。** 调研里最一致的实证是：当 Done-criteria 从散文升级成**可执行检查**（测试、脚本、断言）时，brief 本身就消灭了一大类静默失败——agent 无法对一条红着的测试"自信地宣称完成"。这就是 2025-2026 年 TDD-inversion 潮流的全部内容："tests give us reliable exit criteria"（Willison），"weak tests produce conformant but wrong code"（反过来说：strong tests 让 conformant-but-wrong 无处藏身）。Anthropic 自己的第一条最佳实践就是 "Give Claude a way to verify its work"，官方估计值 2-3x。

**修正后的框架：两个病共享同一个治疗物——契约，但它在两个时刻起效：**

- **编写时刻**（治病1）：意图、边界、升级条件写透 → agent 的自由裁量收敛。你已经做到了。
- **运行时刻**（治病2）：契约里的完成标准被**独立地、机械地执行** → 失败自动举手。你完全没做。

病2 里真正 brief 治不了的只剩两块：① **执行者自证不可信**（你的 `references/dispatch.md` 让执行 agent "对照 Done-criteria 自检并附证据"——这恰好是你自己诊断为不可信的那种自报告，是当前系统里最大的自相矛盾）；② **specification gaming**（agent 把测试改绿而不是把代码改对）。这两块的解法分别是"二钥原则"（§3.2）和"红先绿后"纪律（§3.1）。

X 调研的裁决原话：**spec 质量和验证机制是互补品，不是替代品——没有一个可信的实践者声称单靠其中一个就够**（Horthy 主张 spec 上游论的同时自己也建确定性门禁；Anthropic 把两者列为两条独立的必做项）。

### 1.2 "scale 的瓶颈是检测"：只对了现在这一站

检测确实是**你此刻撞的墙**——因为你的完成标准不可执行、失败不举手，所以你被迫全量巡检。但三路调研都指向同一件事：**检测是最容易自动化的一环，自动化之后瓶颈立刻迁移**。到 2026 年中，跑得最远的实践者（Yegge 20-30 agents、steipete 全天候 loop、Cherny "dozens of Claudes"）全都已经把检测自动化了，而他们仍然堵着——堵在：

1. **Review/landing 吞吐**：steipete："Codex 连跑四天，我勉强跟得上 implementing/testing/landing 所有 PR"；Faros 遥测：PR 量 +98%，review 时长 +91%。
2. **合并串行化**：Yegge："merging has become the new wall"；12+ agents 在 20 万行库上互相覆盖对方的工作。
3. **上游喂养质量**：Gas Town 一周实测报告的结论——"难的是持续喂给系统与你目标对齐、规格良好的任务"。这恰好是 auftrag 的强项，说明你的上半场投资是对的。
4. **认知带宽本身**：Osmani "Your parallel Agent limit"——评估、决策、信任、整合是单线程的；Yegge："你永远是瓶颈。你。不是它们。"

**设计含义**：检测层要建（§3.3），但如果只建检测，你会在三周后回来写一篇"scale 真正的瓶颈是 review"的痛点自述。所以本设计同时给出 review 的分层（§3.2 第三层）和 WIP 上限（§3.3 S4）——检测把"找出翻车的 4 个"变成免费，WIP 上限保证"验收 16 个绿的"不淹死你。

### 1.3 "我只能同时管 2-3 个 session"：数字对，结论错

实测天花板确实低：Yegge 给的数是 3-5 个并行工作流，"有时 2-3 个就把你拖垮"。但突破这个数字的所有人，**没有一个是靠提高自己的注意力上限**——他们全部换掉了管理基质：从"盯 session"换成"管 pipeline"，从轮询换成例外中断（Klaassen："一个什么都能看到的 orchestrator，胜过十二个争夺你注意力的面板……它只在必须时打断你"）。

所以"2-3 个"不是要修的 bug，是交互式监管的物理常数。**正确目标不是同时开 20 个终端，而是：前台永远只有 1 个你正在对话的 session，其余全部在后台跑，靠状态机和推送与你交互。** Claude Code 已原生支持这个形态（§2）。

顺带治好你的"切回 session 忘了要干嘛"：那不是记忆力问题，是**状态存在你脑子里而不是外部**的问题。契约落盘 + 台账 + `/catchup` 命令（§3.3 S3）让重入成本变成 O(1)。

### 1.4 任务三分法：站得住，但轴要换、且要"拆"而不是"分"

三分法（产物在外/在脑/在判断）方向正确，而且你的 Phase 2.5 分诊已经在做。两个精化：

1. **可委托性的操作轴是"验收可否机械化 × 错误可否廉价撤销"，不是"成果落在哪"。** 同样是产物型任务，"重构这个模块（测试全过为准）"是高可委托的，"把落地页改好看"是低可委托的——后者的验收标准在你的审美里，属于你说的第三类。用这根轴，三类任务自然落位，而且能解释为什么有些产物型任务照样反复返工。
2. **大多数真实任务是复合体，正确动作是"拆"，不是"整个归类"。** 学习类可以委托**备菜**（讲义、带注释的代码走读、练习题、搭好的环境），"吃"必须你串行来；决策类可以委托**参谋部作业**（决策备忘录：选项、代价、不可逆性、推荐+置信度），拍板必须你来。所以不是三条隔离的管道，是一条管道 + 两个"可委托部分的提取器"（§3.4）。

### 1.5 你没说、但调研说重要的四个盲区

- **模型诚实度是变量不是常数。** "declaring victory early" 已被 Anthropic 当作头条缺陷在修（Opus 4.8 发布词直接写"catches its own bugs instead of declaring victory early"）。病2 会随模型代际部分自愈——所以验证机制要设计成**可随信任度调松的**（抽查率可调），别焊死。
- **成本与限额是 scale 的一等约束。** Yegge 三个 $200 Max 计划全部打满。你的 WIP 上限同时也是预算上限。
- **你的核心判断没有数据。** "我感觉真正吃掉我的是检测"——这是没有仪表盘的直觉。本设计内置度量（§3.5）：每次返工记录原因分类，四周后你用数据回答"病1病2到底谁大"，而不是用感觉。这是对你"不要默认我的观点是对的"的最终回应：**系统自带检验你假设的仪器。**
- **静默失败的镜像是静默成功。** 绿灯也会骗人（LLM 判官的 false-green 有实证：表面线索能把判官一致性从 69.9 抬到 81.6 而正确性毫无提升）。所以 GREEN ≠ 免检，GREEN = 进入抽查池（§3.2 第三层）。

---

## 2. 设计总纲

```
        你（前台永远只有 1 个对话 session）
        │
        │ ① /auftrag  五格契约（已有，升级：Done-criteria 双轨 + 类型/风险路由字段）
        ▼
   契约 = Todoist 任务（人的视图）+ .claude/auftrag/<id>.md（机器的视图）
        │
        │ ② /dispatch  按类型路由 + WIP 上限检查
        ▼
   执行层：后台 session（claude agents / claude --bg，worktree 隔离，原生守护进程托管）
        │
        │ ③ Stop hook（确定性门禁）：跑契约里的 verify 命令，不过 → 不许停，差距喂回去
        ▼
   验证层：/abnahme 独立验证者（fresh context 对抗式二审，执行者永远不能给自己盖绿章）
        │
        │ ④ 裁决写台账：GREEN-unreviewed / RED / BLOCKED
        ▼
   注意力路由：Todoist labels + 评论证据（todoist-sync 已有一半）
        │         + Notification hook（agent_needs_input / agent_completed）
        │         + Remote Control 手机推送（原生，带在场检测防打扰）
        ▼
   你的一个收件箱：/board（例外队列：决策 > RED > GREEN 抽查）+ /catchup（O(1) 重入）
```

四条铁律，全部来自调研共识：

1. **信任分层**：确定性检查 > 独立 LLM 验证者 > 执行者自报告。LLM 判官只做参考裁决，永远不做唯一绿灯。
2. **二钥原则**：干活的 agent 不能给自己盖 GREEN；裁决者必须是 fresh context。
3. **例外管理**：你从不轮询；只有状态**转移**才打扰你，且按"阻塞你 > 阻塞它 > 不阻塞"排序。
4. **投资模式不投资工具**：一年内 Crystal 弃、Terragon 死、Omnara 归档、vibe-kanban 转手。凡官方原生有的（舰队面板、推送、门禁钩子）一律用原生，自建的只有胶水（契约格式、验证者 prompt、台账）——这些是模式，搬到任何未来工具上都成立。

---

## 3. 组件明细

### 3.1 契约升级（治病1，同时给病2铺轨）—— 改 auftrag，动作最小

**U1 · Done-criteria 双轨制。** 第五格从散文升级为两栏：

```markdown
## Done-criteria / evidence
verify:                      # 机器轨：命令，exit 0 = 过；这是 Stop hook 与验证者共用的判据
  - uv run pytest tests/test_sync.py -q
  - ./scripts/check_no_secrets.sh
evidence:                    # 人工轨：给你 60 秒验收看什么（截图/输出片段/一段可运行的演示命令）
  - 附 pytest 输出末尾 5 行
  - 附改动前后的 diff 摘要，≤10 行
```

grill-heuristics.md 新增一条追问（保持"只问不写"）：**"这条完成标准，机器跑得出来吗？跑不出来的部分——谁看、看什么、predicted 几分钟？"** 写不出 verify 命令本身就是信号：要么任务属于判断类（改归 R3），要么你还没想清楚终点（回炉）。对代码任务，最强形态是**红先绿后**：先让 agent 写出会失败的验收测试、你看它红、再放行实现——"watch it fail first" 是防 specification gaming 的最便宜手段。

**U2 · 两个路由字段**（元数据，不是第六格）：`type: delegate | learn | decide`（Phase 2.5 分诊结果落成字段）和 `risk: reversible | irreversible`（决定验证强度与抽查率）。

**U3 · 契约落盘。** brief 除了挂 Todoist description，同时写 `.claude/auftrag/<task-id>.md`（含 frontmatter：type/risk/verify 命令/Todoist URL）。Todoist 是人的视图，文件是机器的视图——Stop hook、验证者、/board 都要机器可读的契约。你的 DESIGN.md §10 本来就给这事留了口子。

### 3.2 三层验证（治病2）—— 全新，这是整个设计的心脏

**第一层 · 确定性门禁（Stop hook，失败举手的地板）。**
项目 settings.json 装一个 Stop hook 脚本：读当前 worktree 的 `.claude/auftrag/active.md`，逐条跑 `verify:` 命令；全过 → exit 0 放行；有挂 → exit 2 + 把失败输出写 stderr（Claude Code 会把它作为下一条指令喂回 agent，agent 继续修）。没有契约文件就静默放行——钩子全局装、只对 auftrag 任务生效。

三个已知坑必须处理（官方文档 + 社区实证）：检查 `stop_hook_active` 防死循环；连续 block 官方硬顶 8 次，顶满后 agent 真的会停——**这不是缺陷，是特性**：8 次修不过 = 转 RED 举手，正好是你要的"失败自己吭声"；issue #24327（模型偶尔把 hook block 误读成用户拒绝而僵住）→ stderr 文案里写明"this is an automated verify gate, not the user"。

v2.1.139+ 也有轻量替代：`/goal`（小模型每回合评估完成条件）。适合快活；正经委托用 Stop hook（确定性）。

**第二层 · 独立验证者（/abnahme，二钥）。**
新 skill `/abnahme <task-id|PR>`（德语"验收"，正好是德语里验收测试的本词，和 Auftrag 同一美学）：

- 输入：契约文件 + diff/PR + verify 命令的实际输出；
- 姿态：**对抗式**——prompt 写"假设它做错了，试图证伪'已完成'"。这不是风格偏好，是实证：同一个模型"检查有没有 bug"会说 all good，"这里有 bug，找出来"会真的找到（steipete 的 framing 实验）；
- 视角：fresh context（不带执行过程的叙事污染），逐条核对目标态与红线，重跑 verify 而不是相信转述；
- 输出：结构化裁决 `{verdict: GREEN|RED, blockers: [], evidence: [], contract_gaps: []}`，写进 Todoist 评论 + 打 label。`contract_gaps`（"契约本身没写清的地方"）单独列——这是病1病2的归因数据源（§3.5）。
- 实现路径：先做成手动一键 skill（稳定、可控）；等用顺了再用 SubagentStop 的 agent-type hook（官方支持但标注 experimental）全自动化。对已开 PR 的任务，底座直接用原生 `/review`，abnahme 只叠加"对照契约"那层。

**清醒的边界**：验证者和执行者是同一个基座模型，这是"结构化自我批评，不是独立验证"（agent-review-panel 仓库的诚实注脚）。缓解手段就是把它锚死在**工件**上（契约、测试输出、diff），不许它发表印象派意见。最终裁决链 = 确定性检查过 && 验证者无 blocker && （高风险任务）你抽查过。

**第三层 · 人的分层验收（治"全量检查"）。**
GREEN ≠ 免检，GREEN = 进抽查池。规则借制造业验收抽样：`risk: irreversible` → 100% 人查；新任务类型头 5 个 → 100% 查（校准期）；校准过的可逆任务 → 抽 1/3，逐步降到 1/5；发现一次 false-green → 该类型抽查率立刻打回 100%。每次人查只看 `evidence:` 栏定义的 60 秒材料，不重读全部产出——**验收成本在写契约时就被定价了**。

### 3.3 注意力路由（治 scale·检测→治 scale·注意力）

**S1 · 舰队面板用原生的，不自建。** `claude agents`（GA）就是你的作战室：所有后台 session 四态一屏（Working / Needs input / Ready for review / Completed），Space 偷看、Enter 接管、完事后台自动 commit + push + 开 draft PR（v2.1.198）。日常形态：**1 个前台对话 session + N 个后台执行 session**，多终端时代结束。vibe-island/notchi 保留当氛围灯，但语义通知走下面这条新通道。

**S2 · 语义推送，只推状态转移。** 三通道按紧急度：

| 状态转移 | 含义 | 通道 |
|---|---|---|
| → BLOCKED | 升级条件命中，**它在等你** | 手机即时推送（Remote Control 原生推送，v2.1.110+，带在场检测：你在键盘前就不推） |
| → RED | 8 次门禁没过 / 验证者拒收 | 即时推送 |
| → GREEN-unreviewed | 完成待验收，不急 | 静默入队，攒批处理 |

实现：打开 `agentPushNotifEnabled`（你现在是 **false**——这是全设计里性价比最高的一次 settings 改动）+ Notification hook 监听 `agent_needs_input` / `agent_completed`（v2.1.198 起后台 agent 原生发这两个事件）转发 Discord/ntfy。

**S3 · 一个收件箱：/board + /catchup。**
`/board`（薄 skill）：读 Todoist labels + 台账，渲染一屏例外队列，排序 = **决策（阻塞 agent，最贵）> RED（要重派）> GREEN（攒批验收）**，每行一句"等你什么 + predicted 处理分钟数"。Todoist 侧建同构 filter（`@agent:blocked | @agent:red | @agent:green-unreviewed`），手机上也能看。
`/catchup <task-id>`：读契约 + 最新裁决 + session 状态，三段式输出（当初为什么派 / 现在到哪了 / 此刻要你做什么），30 秒重入。治"切回来忘了要干嘛"。

**S4 · WIP 上限（这条最反直觉但证据最硬）。** 同时 in-flight 的 delegate 任务数 ≤ 你当天能验收的量。**起步 = 3**，用台账数据调。dispatch 时检查：满了 → 默认走 store（auftrag 本来就有存档路径，现在它有了真正的作用：缓冲队列）。依据：并行度超过验收吞吐只是把 WIP 变陈旧 + Osmani 的"超过上限你不是在 review，你只是在 accept——感觉不像失败，感觉像高产"。

**S5 · 串行合并。** 一次只 land 一个 PR（全行业共识，从 Gas Town 的 refinery 到 Paola 的 sequencing）。worktree 隔离原生有（`isolation: worktree` / `claude -w`），合并永远走你的手。

### 3.4 类型路由（治横切）

`/dispatch` 读 `type:` 字段走三条路：

- **delegate** → 全流水线（3.1→3.2→3.3）。
- **learn** → **备菜管道**：agent 产出学习包（讲义/带注释的代码走读/练习题+答案/搭好的环境），学习包本身要过最小 verify（引用的文件行号真实存在、习题可运行——防幻觉教材）；产出后任务转到"你的串行队列"，**不并行、不进舰队、不推送**。Done-criteria 是你的自测（"我能不看材料把 X 讲一遍"），永远不是 agent 的完成。
- **decide** → **参谋部管道**：agent 产出决策备忘录，固定模板：≥2 个真选项 / 每项代价与不可逆性 / 推荐 + 置信度 / **"什么新信息会翻转这个推荐"**（最后一条是好参谋的签名）。你拍板后，决定往往直接变成下一份 Auftrag——两个 skill 天然串联。
- **统一升级形态**：BLOCKED 的 agent 停下来时，产出物就按参谋部模板写——于是你的决策队列里每一项长得一样，拍板速度最大化。这正是 dispatch.md 已有的"halt-and-return"的升级版。

### 3.5 度量（治"我感觉"）

台账 `~/.claude/auftrag/ledger.jsonl`，每任务终局一行：

```json
{"id":"...","type":"delegate","risk":"reversible","outcome":"green|red|blocked|aborted",
 "rework_reason":"brief-gap|silent-execution-error|verifier-missed|changed-my-mind|null",
 "verify_mode":"executable|manual","cycle_h":6.5,"escalations":1}
```

`/retro`（月度，或攒 20 个任务跑一次）：返工原因分布、false-green 率、平均验收耗时、WIP 建议。**这个分布直接裁决你的两病假设**：`brief-gap` 占大头 → 回去磨 grill-heuristics；`silent-execution-error` 占大头 → 你是对的，加强验证层；`changed-my-mind` 占大头 → 问题在你，不在系统。

### 3.6 明确不做清单（和做的清单一样重要）

- **不自建看板/面板工具**：原生 agent view + Todoist filter 覆盖；社区同类工具一年死一批。
- **不上 Gas Town / claude-flow 式 20-30 agent 蜂群**：成本（三个 Max 打满）、对齐喂养难、以及你的任务量根本不需要。Ronacher 的实验负结果：implementation loop 在中型真实项目上还不成立——loop 只用于 review/research。
- **不做常驻 orchestrator daemon**：你的场景是"少量高质量委托"，不是吞吐最大化；一个前台 session + 原生后台守护进程足够。
- **不用 agent teams（暂时）**：仍是 experimental、`/resume` 不恢复 teammates、token 按队员线性烧。等 GA 重估。
- **auftrag skill 本身不加 hook、不变成系统**：见 §5。

---

## 4. 分阶段落地

**阶段 0 · 本周末，约半天，只动刀口上的肉：**
1. settings：`agentPushNotifEnabled: true` + 配 Remote Control（5 分钟，立刻获得"失败举手"的手机端）。
2. auftrag 升级 U1/U2/U3（双轨 done-criteria + 路由字段 + 契约落盘）——改的是 SKILL.md 与 grill-heuristics.md 的问法，半小时。
3. 写 Stop hook 脚本（读契约跑 verify，~40 行 shell/python）装进项目 settings。
4. 执行形态切换：下一个 delegate 任务不再开新终端，用 `claude agents` 派后台 session。
   **退出标准**：跑通 3 个真实任务，其中至少 1 个失败案例是推送告诉你的，而不是你巡检发现的。

**阶段 1 · 两周后（有 5-10 个任务的手感了）：**
/abnahme 验证者 + /board + /catchup + WIP=3 生效 + learn/decide 两条子管道模板成形 + 台账开始记录。

**阶段 2 · 一个月后（有 20+ 条台账数据）：**
跑 /retro，让数据决定下一步：加强验证层，还是回炉 brief 质量，还是发现瓶颈已迁移到 review——届时再决定要不要抽查率自动化、SubagentStop 全自动验证、cron 夜间 verify sweep（Routines/desktop scheduled tasks 都是现成的）。

---

## 5. 与现有仓库的衔接（一个原则性冲突的裁决）

CONCEPT.md 边界 #2 说"别急着上 hook、上校验脚本"，边界 #3 说"别做成系统"。本设计没有推翻它们，而是划清了辖区：

- **auftrag = 契约的 authoring 层**，保持纯 prompt、只问不写、不上 hook——原始边界原封不动。它管的是"派出去之前"。
- **新组件（Stop hook / abnahme / board / ledger）= 运行时的 enforcement 层**，是独立的兄弟模块，管的是"派出去之后"。静默失败不是访谈流程上的洞，是 dispatch 之后那个世界里的洞——当初"用过十几回再精准补"的条件，现在已经满足了：你天天在被它拽回去返工。
- 仓库形态建议：auftrag 保持现状；新增兄弟目录（如 `abnahme/`、`hooks/`），或者干脆把整个仓库升格为一个 plugin（skills + hooks + agents 打包，Claude Code 插件机制原生支持），`auftragstaktik` 这个仓库名本来就装得下整套指挥体系。

命名建议（延续你的普鲁士美学，克制使用）：派 = **Auftrag**（已有）· 验 = **Abnahme**（德语工程验收/验收测试的本词）· 报 = **Meldung**（/board 输出的战报）。

---

## 6. 证据附录（关键来源）

**官方能力（全部验证于 2026-07-03，v2.1.201）**
- Hooks 参考（Stop/SubagentStop exit-2 门禁、stop_hook_active、8-block cap、prompt/agent 型钩子）: code.claude.com/docs/en/hooks
- 最佳实践（"给 Claude 验证手段"的四级阶梯 + 对抗式 review + Writer/Reviewer）: code.claude.com/docs/en/best-practices
- 舰队面板 agent view: code.claude.com/docs/en/agent-view · 后台 agent 完成/求助原生通知：CHANGELOG v2.1.198
- Remote Control 手机推送（在场检测）: code.claude.com/docs/en/remote-control
- /goal: code.claude.com/docs/en/goal · Routines: code.claude.com/docs/en/routines
- 长任务 harness 设计: anthropic.com/engineering/effective-harnesses-for-long-running-agents · anthropic.com/engineering/harness-design-long-running-apps

**实践者一手经验（X）**
- 3-5 并行认知天花板 + "你永远是瓶颈": x.com/Steve_Yegge/status/1949889158505517288
- 静默失败战例（安全系统忘了说）: x.com/Steve_Yegge/status/1964805936742384063
- framing 效应（"找 bug"vs"有 bug"）: x.com/steipete/status/2060672154727825718
- autoreview 前置 + QA agent 开真 app: x.com/steipete/status/2059453909819654554
- 一个 orchestrator > 十二个面板: x.com/kieranklaassen/status/2053986252610031824
- "关掉笔记本就死的不是 agentic，是 babysitting": x.com/kieranklaassen/status/2057205174960292245
- spec 上游论（review 堵 = spec 投资不足）: x.com/dexhorthy/status/2068734942780244302
- loop 只对 review/research 成立的负结果: x.com/mitsuhiko/status/2068657029443363136
- 红绿 TDD for agents: x.com/simonw/status/2058992972734341445

**社区/研究**
- LLM 判官 false-green 实证（表面线索抬一致性不抬正确性）: arxiv.org/html/2604.16790v1
- Stop hook 完成门禁模式与坑: claudefa.st/blog/tools/hooks/stop-hook-task-enforcement · github.com/anthropics/claude-code/issues/24327
- 认知并行上限与"vigilance tax": addyosmani.com/blog/cognitive-parallel-agents
- Gas Town 一周实测（上游喂养才是难点）: tenzinwangdhen.com/posts/gastown-good-bad-ugly
- METR RCT 及 2026-02 追踪: metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study · metr.org/blog/2026-02-24-uplift-update
- WIP 上限用于 agent 舰队: mindstudio.ai/blog/iterative-kanban-pattern-ai-agents-feedback-loop
- 工具死亡名单（一年内）：Crystal 弃、Terragon 关、Omnara 归档、vibe-kanban 转社区——投资模式不投资工具。
