# Brain-Orchestrator Architecture

> 自动化 Alpha 研究流水线 — 从 Idea 生成到回测验证的全自动循环系统

---

## 1. 系统概述

Brain-Orchestrator 是一个 6 阶段自动化 Alpha 研究流水线，构建在 WorldQuant BRAIN 平台之上。它通过 LLM (大语言模型) 驱动的决策和 BRAIN API 回测，实现从 Idea 生成 → 检查 → 回测 → 决策 → 增强 → 实现的全自动循环。

```
GENERATE → INSPECT → SIMULATE → DECIDE → ENHANCE → IMPLEMENT
    ↑                                                    │
    └────────────────── 循环 ──────────────────────────────┘
```

### 核心设计原则

- **工件驱动 (Artifact-Driven)**: 阶段间通过文件 (JSON/CSV) 通信，不依赖内存变量
- **状态持久化**: `state.json` + `pool.json` + `activity_log.jsonl` 实现断点续传
- **并行流水线**: INSPECT+SIMULATE 逐 Idea 处理，DECIDE 后台并行不阻塞
- **SSE 实时推送**: 前端通过 Server-Sent Events 实时展示流水线进度
- **可中断回测**: 每轮回测支持中断 (abort)，前端一键取消长时间运行的回测

---

## 2. 文件清单与相对路径

> 所有路径相对于 `APP/` 目录 (即 `untracked/APP/`)

### 2.1 核心模块 (brain-orchestrator/)

| 文件 | 相对路径 | 说明 |
|------|----------|------|
| 主循环引擎 | `brain-orchestrator/pipeline_runner.py` | 流水线生命周期、主循环编排、状态持久化、SSE、注册表 |
| Idea 池管理器 | `brain-orchestrator/pool_manager.py` | 线程安全的 Idea 池 CRUD + 统计 |
| 检查阶段 | `brain-orchestrator/stage_inspect.py` | 解析 Idea → LLM 选参 → alpha_list.json |
| 回测阶段 | `brain-orchestrator/stage_simulate.py` | 包装 BatchSimulator + CSV 摘要统计 |
| 决策阶段 | `brain-orchestrator/stage_decide.py` | 规则预过滤 + LLM 选择增强策略 |
| 增强阶段 | `brain-orchestrator/stage_enhance.py` | 调用 enhance_template.py 子进程 |
| 实现阶段 | `brain-orchestrator/stage_implement.py` | 调用 implement_idea.py 子进程 |
| 架构文档 | `brain-orchestrator/ARCHITECTURE.md` | 本文档 |

### 2.2 供应商脚本 (brain-orchestrator/scripts/vendor/)

| 文件 | 相对路径 | 说明 |
|------|----------|------|
| BRAIN API 会话 | `brain-orchestrator/scripts/vendor/ace_lib.py` | 认证、会话管理、sim API |
| 批量回测引擎 | `brain-orchestrator/scripts/vendor/batch_simulator.py` | multi-sim 提交 + 轮询 + CSV |
| 构建 Alpha 列表 | `brain-orchestrator/scripts/vendor/build_alpha_list.py` | 生成 alpha_list.json |
| 获取回测选项 | `brain-orchestrator/scripts/vendor/fetch_sim_options.py` | 从 BRAIN API 查可用参数 |
| 辅助函数 | `brain-orchestrator/scripts/vendor/helpful_functions.py` | 通用工具函数 |
| 凭据加载 | `brain-orchestrator/scripts/vendor/load_credentials.py` | 读取 BRAIN 凭据 |
| Idea 文件解析 | `brain-orchestrator/scripts/vendor/parse_idea_file.py` | 解析 idea_*.json |
| 参数解析 | `brain-orchestrator/scripts/vendor/resolve_settings.py` | LLM 辅助选择回测参数 |
| 表达式校验 | `brain-orchestrator/scripts/vendor/validator.py` | Alpha 表达式语法校验 |

### 2.3 外部依赖脚本 (trailSomeAlphas/)

> 这些脚本位于 `brain-orchestrator/` 的父目录 `APP/` 下

| 文件 | 相对路径 | 被谁调用 | 说明 |
|------|----------|----------|------|
| GENERATE 脚本 | `trailSomeAlphas/run_pipeline.py` | `pipeline_runner.py` → `phase_generate()` | LLM 生成初始 Idea |
| 增强脚本 | `trailSomeAlphas/enhance_template.py` | `stage_enhance.py` → `enhance()` | 模板 single/cross 增强 |
| 实现脚本 | `trailSomeAlphas/scripts/implement_idea.py` | `stage_implement.py` → `implement()` | 增强模板 → 新 Idea |

### 2.4 Web 层

| 文件 | 相对路径 | 说明 |
|------|----------|------|
| Flask 主应用 | `运行打开我.py` | 所有 HTTP/API 路由入口 |
| 控制面板模板 | `templates/pipeline_dashboard.html` | 流水线 Dashboard 前端 (创建/监控/操作) |

### 2.5 运行时数据 (brain-orchestrator/pipelines/)

```
brain-orchestrator/pipelines/<pipeline_id>/
├── config.json                  # 流水线配置 (不含敏感信息)
├── state.json                   # 检查点状态
├── pool.json                    # Idea 池
├── activity_log.jsonl           # 活动日志 (JSONL 格式，追加写入)
├── sim_options_snapshot.json    # 回测选项快照
├── gen/                         # GENERATE 产出的 idea_*.json
├── inspect/<idea_stem>/         # INSPECT 产出
│   ├── alpha_list.json
│   ├── chosen_settings.json
│   ├── idea_context.json
│   └── settings_candidates.json
├── sim/                         # SIMULATE 产出的 CSV
├── enhance/round_N/             # ENHANCE 产出
│   ├── decision.json
│   ├── enhanced_templates_*.json
│   └── enhanced_final_expressions_*.json
└── implement/round_N/           # IMPLEMENT 产出的新 idea_*.json
```

---

## 3. 模块详解

### 3.1 pipeline_runner.py — 主循环引擎

> 文件路径: `brain-orchestrator/pipeline_runner.py`

**职责**: 流水线生命周期管理、主循环编排、状态持久化、SSE 推送、流水线注册表、回测中断

#### 核心类

##### `PipelineState`
- 封装 `state.json` 的读写
- 线程安全 (`threading.Lock`)
- 原子写入 (写入 `.tmp` 后 `replace`)
- 存储: `status`, `phase`, `iteration`, `error`, `last_checkpoint` 等

##### `PipelineRunner`
- 每个流水线一个实例
- 主要属性:
  - `pipeline_id`, `pipeline_dir`, `config` — 标识和配置
  - `state: PipelineState` — 检查点状态
  - `pool: PoolManager` — Idea 池
  - `_stop_event: threading.Event` — 优雅停止信号
  - `_activity_log: deque(maxlen=500)` — 内存日志缓存
  - `_log_path` — JSONL 日志文件路径
  - `_subscribers: list[queue.Queue]` — SSE 订阅者
  - `_abort_ideas: set` — 已请求中断的 Idea 文件集合 (线程安全)

- 主要方法:
  - `start()` / `stop()` — 启动/停止后台线程
  - `log_activity(msg, level, phase)` — 记录日志 → 持久化 → SSE 广播
  - `subscribe()` / `unsubscribe()` — SSE 订阅管理
  - `status()` — 返回当前状态快照 (含 `decide_prompt`)
  - `abort_idea(idea_file)` — 中断指定 Idea 的回测
  - `_is_idea_aborted(idea_file)` — 检查 Idea 是否被中断
  - `_run_loop()` — **核心循环** (见下文)

#### 主循环 `_run_loop()` 流程

```
1. 创建 BRAIN 会话 (ace_lib)
2. if 首次运行 (iteration=0, 池为空):
   │  GENERATE → 产出 idea_*.json → 加入池
3. while not stop_event:
   │  iteration += 1
   │  重新认证 BRAIN 会话
   │
   │  ┌─ 补回测: 处理上轮遗留的 pending_sim
   │  │
   │  ├─ 初始化后台 DECIDE 线程管理
   │  │
   │  ├─ for each pending_inspect idea:  ← 逐 Idea 流水线
   │  │   ├─ INSPECT (LLM 选择回测参数)
   │  │   ├─ SIMULATE (提交 BRAIN 回测)
   │  │   └─ _spawn_decide_if_ready()  ← 后台启动 DECIDE
   │  │
   │  ├─ 补回测: 处理遗漏的 pending_sim
   │  │
   │  ├─ 等待后台 DECIDE 完成 + 收集结果
   │  │
   │  ├─ 最终 DECIDE: 处理剩余未决策候选
   │  │   └─ DECIDE → ENHANCE → IMPLEMENT
   │  │
   │  ├─ 新 Idea 加入池
   │  │
   │  └─ 错误恢复 (重试失败的 INSPECT/SIM)
```

#### 并行策略 — 核心架构亮点

系统的回测并行模型是整个流水线效率的关键。设计目标：**多个 Idea 同时占用 BRAIN 平台的多个回测卡槽，最大化吞吐量**。

##### 两层并行架构

```
                          phase_simulate()
                               │
              ThreadPoolExecutor(max_workers=sim_concurrent)
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
         Worker-1           Worker-2           Worker-N
         (Idea A)           (Idea B)           (Idea ...)
             │                 │                 │
     simulate_idea()    simulate_idea()   simulate_idea()
     concurrency=1      concurrency=1     concurrency=1
             │                 │                 │
     BatchSimulator      BatchSimulator    BatchSimulator
     ┌──────────┐       ┌──────────┐      ┌──────────┐
     │batch 1→2→│       │batch 1→2→│      │batch 1→2→│
     │→3→...    │       │→3→...    │      │→3→...    │
     │(顺序提交) │       │(顺序提交) │      │(顺序提交) │
     └──────────┘       └──────────┘      └──────────┘
```

| 层级 | 并行方式 | 控制参数 | 说明 |
|------|----------|----------|------|
| **跨 Idea 并行** | `ThreadPoolExecutor` | `sim_concurrent` | N 个 Worker 同时回测 N 个不同 Idea，每个占 1 个 BRAIN concurrent 额度 |
| **Idea 内顺序** | 单线程循环 | `sim_multi_slots` | 每个 Worker 内部，Alpha 按 `sim_multi_slots` 分批，逐批提交 multi-sim，等待结果后再提交下一批 |

##### 关键设计决策

1. **1 Idea = 1 Worker = 1 concurrent 额度**
   - 每个 `simulate_idea()` 内部 `BatchSimulator.run(concurrency=1)`
   - 保证每个 Idea 恰好占用 BRAIN 平台 1 个并发卡槽
   - `sim_concurrent` 个 Idea 同时跑 = 占用 `sim_concurrent` 个卡槽

2. **全局 Worker 额度限制 (GLOBAL_WORKER_LIMIT=8)**
   - 所有运行中流水线的 `sim_concurrent` 之和不超过 8
   - 前端可动态 +/- 调整每条流水线的 Worker 数
   - 后端 `global_worker_usage()` 实时统计已占用额度

3. **`phase_simulate()` 是并行化的入口**
   - 收集所有 `pending_sim` 的 Idea
   - 提交到 `ThreadPoolExecutor(max_workers=sim_concurrent)`
   - `as_completed()` 等待所有 Worker 完成
   - 每个 Worker 独立调用 `simulate_idea()` → `BatchSimulator`

4. **INSPECT+SIM 流水线中的串行回测**
   - 主循环的 `for each pending_inspect` 中，INSPECT 后立即串行调用单个 `simulate_idea()`
   - 这是"检查一个跑一个"的流水线模式，不走 ThreadPoolExecutor
   - 仅 `phase_simulate()` (补回测阶段) 使用并行

##### 各阶段并行总结

| 阶段 | 并行方式 | 说明 |
|------|----------|------|
| INSPECT | **ThreadPoolExecutor(max_workers=5)** | 所有 pending_inspect 并行检查，完成后统一进入回测 |
| SIMULATE (补回测) | **ThreadPoolExecutor** | `sim_concurrent` 个 Worker 并行跑不同 Idea |
| SIMULATE (主循环后) | **ThreadPoolExecutor** | INSPECT 全部完成后，所有新 pending_sim 一起并行回测 |
| DECIDE | 后台线程 | SIM 完成后自动触发，与 INSPECT+SIM 并行 |
| ENHANCE | 顺序 | 在 DECIDE 线程内顺序增强 |
| IMPLEMENT | 顺序 | 每个增强模板顺序实现 |

后台 DECIDE 使用独立的 BRAIN 会话 (`_decide_session`)，避免与主线程的会话冲突。

##### 优雅 Worker 缩减

当用户在前端动态减少 `sim_concurrent` 时，已在运行的 Worker 不会被强制终止。`phase_simulate()` 向每个 Worker 传递 `get_worker_limit` 回调，Worker 在 `claim_for_sim()` 前检查当前 running 数是否已达新上限，若已达则主动退出不再领取新 Idea。

##### Retry 即时触发

`retry_idea()` 将 Idea 状态重置为 `pending` 后，立即调用 `trigger_sim()` 在后台线程启动 `phase_simulate()`，保证被重试的 Idea 不必等到主循环下一次迭代才被处理。

#### 流水线注册表 (模块级函数)

- `create_pipeline(config)` → 创建目录 + PipelineRunner 实例 + 注册
- `get_pipeline(pipeline_id)` → 查询注册表
- `list_pipelines()` → 所有流水线状态列表
- `load_existing_pipelines()` → 启动时扫描 `pipelines/` 恢复已有流水线
- 注册表 `_pipelines: dict[str, PipelineRunner]` 由 `_registry_lock` 保护

#### 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `region` | 市场区域 (USA/CHN/EUR/ASI/GLB) | — |
| `delay` | 交易延迟 (0 或 1) | — |
| `universe` | 股票池 (TOP500/TOP3000 等) | — |
| `data_type` | 数据类型 (MATRIX/VECTOR) | MATRIX |
| `dataset_id` | 数据集 ID | — |
| `data_category` | 数据集分类 | — |
| `sim_concurrent` | 并发 Idea Worker 数 (同时跑几个 idea, 每个占 1 个 concurrent 额度) | 2 |
| `sim_multi_slots` | 每个 Worker 每批提交的 Alpha 数 | 2 |
| `max_enhance_per_round` | 每轮最大增强数 | 4 |
| `moonshot_api_key` | LLM API Key | — |
| `moonshot_base_url` | LLM API URL | `https://api.moonshot.cn/v1` |
| `moonshot_model` | LLM 模型名 | `kimi-k2.5` |
| `prompt_overrides` | 按阶段自定义 system prompt 的覆盖字典；只在创建该流水线时固化到 `config.json` | `{}` |
| `stop_conditions` | 自动停止条件配置；创建时可设置，运行中也可热更新；默认全部关闭 | 见下方结构 |
| `decide_prompt` | 旧版决策提示词覆盖字段；仍兼容，但优先级低于 `prompt_overrides.decide_system_prompt` | `""` |
| `brain_username` / `brain_password` | BRAIN 平台凭据 (仅运行时，不持久化) | — |

`prompt_overrides` 当前支持的 key:
- `generate_system_prompt`
- `inspect_settings_system_prompt`
- `inspect_repair_system_prompt`
- `decide_system_prompt`
- `enhance_single_system_prompt`
- `enhance_cross_system_prompt`

`stop_conditions` 当前支持的 key:

- `sharpe_target_count.min_sharpe` + `sharpe_target_count.target_count`: 达到足够多的高 Sharpe 结果时停止
- `max_pool_ideas`: 池中 Idea 总数上限
- `max_alpha_submitted`: 累计回测提交量上限
- `max_sim_completed`: 累计回测完成量上限
- `max_iterations`: 主循环最大迭代数
- `diminishing_returns`: 最近若干轮增强的合格率低于历史基线一定比例时停止

---

### 3.2 pool_manager.py — Idea 池管理器

> 文件路径: `brain-orchestrator/pool_manager.py`

**职责**: 追踪所有 Idea 的生命周期状态，线程安全，JSON 持久化

#### `PoolEntry` (dataclass)

| 字段 | 类型 | 说明 |
|------|------|------|
| `idea_file` | str | 相对路径 (如 `ideas/idea_001.json`) |
| `origin` | str | 来源: `"gen"` 或 `"enhance_round_N"` |
| `enhanced_from` | list[str] | 父 Idea 文件列表 |
| `inspect_status` | str | `pending` → `done` / `error` |
| `alpha_list_file` | str | INSPECT 产出的 alpha_list.json 路径 |
| `sim_status` | str | `pending` → `running` → `done` / `error` |
| `sim_csv` | str | SIMULATE 产出的 CSV 路径 |
| `sim_summary` | dict | `{count, completed, sharpe_avg, sharpe_var, fitness_avg, fitness_var, turnover_avg}` |
| `enhance_selected` | bool | 是否被 DECIDE 选中进行增强 |
| `error` | str | 错误信息 |

#### Idea 状态机

```
                    ┌──────────┐
        add()  ──→  │ pending  │  (inspect_status)
                    └────┬─────┘
                         │ inspect_idea()
                    ┌────▼─────┐
                    │   done   │  ──→  sim_status: pending
                    └────┬─────┘
                         │ simulate_idea()
                    ┌────▼─────┐
                    │ running  │  (sim_status)
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
     ┌────▼─────┐   ┌───▼──────┐  ┌────▼─────┐
     │   done   │   │ aborted  │  │  error   │  (可重试)
     └────┬─────┘   └──────────┘  └──────────┘
          │ decide()
     ┌────▼──────────┐
     │enhance_selected│
     └───────────────┘
```

#### 查询方法

- `pending_inspect()` — inspect_status == "pending"
- `pending_sim()` — inspect_status == "done" AND sim_status == "pending"
- `simulated()` — sim_status == "done"
- `candidates_for_enhance()` — sim_status == "done" AND NOT enhance_selected
- `stats()` — 统计摘要

---

### 3.3 stage_inspect.py — 检查阶段

> 文件路径: `brain-orchestrator/stage_inspect.py`

**职责**: 解析 Idea JSON → 获取回测选项 → LLM 选择最佳参数 → 生成 alpha_list.json

**流程**:
1. `parse_idea_file.py` 解析 idea_*.json 提取表达式和元数据
2. `fetch_sim_options.py` 从 BRAIN API 获取可用回测选项 (Region/Delay/Universe/Neutralization等)
3. `resolve_settings.py` + LLM 选择最佳回测参数组合
4. `validator.py` 校验表达式语法
5. `build_alpha_list.py` 生成 alpha_list.json

**重试语义**:
- `retry_inspect_idea()` 不只是重新执行同一份 inspect 流程；当 `idea_context.json` 中没有任何有效表达式，但存在 `validation_failures` 时，会进入 LLM 修复模式
- 修复触发条件覆盖运算符/签名错误，也覆盖 `非法字符`、`语法错误`、`无法解析表达式` 等语法级失败
- 若当前 `expression_list` 全部失效，LLM 允许基于 `template + idea + validation_failures` 直接重生成新的 `expression_list`
- LLM 修复调用使用更长的读取超时，避免复杂修复任务过早超时

**提示词覆盖与传参细节**:
- `inspect_settings_system_prompt` 仅覆盖选参阶段的 system prompt 文本
- 可选 `neutralization/universe/decay` 不是插值到 system prompt 里的变量，而是作为 user prompt JSON 的 `candidates` 字段传给 LLM
- 当流水线固定了 `universe` 时，`_llm_choose_settings()` 会先过滤候选，再把过滤后的 `candidates` 发给模型
- `inspect_repair_system_prompt` 仅用于 LLM 修复/重生成非法表达式的 system prompt

**输入**: `idea_*.json`  
**输出**: `inspect/<stem>/alpha_list.json`

---

### 3.4 stage_simulate.py — 回测阶段

> 文件路径: `brain-orchestrator/stage_simulate.py`

**职责**: 包装 BatchSimulator，对单个 Idea 提交回测并收集结果

**核心函数**: `simulate_idea()`
- 接收一个 Idea 的 `alpha_list.json` 和输出 CSV 路径
- 创建 `BatchSimulator(session, cancel_check=...)`
- 调用 `simulator.run(alpha_list, batch_size=sim_multi_slots, concurrency=1)`
- **`concurrency=1`**: 保证每个 Idea 恰好占用 1 个 BRAIN 并发卡槽
- 回测结果写入 CSV，返回摘要 dict

**关键参数**:
- `sim_multi_slots` — 每个 Worker 每批提交的 Alpha 数量 (multi-sim batch size)
- `cancel_check` — 可选回调函数，用于中断检查
- `progress_callback` — 每批完成后回调，用于增量更新池中的 sim_summary

**并行调度**: `simulate_idea()` 本身是单线程的。跨 Idea 的并行由 `pipeline_runner.py` 中的 `phase_simulate()` 通过 `ThreadPoolExecutor(max_workers=sim_concurrent)` 实现（详见 §3.1 并行策略）。

**CSV 摘要统计** (`_summarize_csv`):
- `count` — Alpha 总数
- `completed` — 成功完成的回测数
- `sharpe_avg` — Sharpe 均值
- `sharpe_var` — Sharpe 方差 (用于前端 `均值(方差)` 展示)
- `fitness_avg` — Fitness 均值
- `fitness_var` — Fitness 方差
- `turnover_avg` — Turnover 均值

**CSV 命名**: `_sim_csv_name()` 辅助函数为增强轮次产出的 Idea 自动添加 `round_N_` 前缀，避免同名 Idea 在不同轮次产生 CSV 路径冲突。

**输入**: `alpha_list.json`
**输出**: `sim/<stem>_simulation_status.csv` (增强 Idea 为 `sim/round_N_<stem>_simulation_status.csv`) + 摘要 dict

---

### 3.5 stage_decide.py — 决策阶段

> 文件路径: `brain-orchestrator/stage_decide.py`

**职责**: 从已回测候选中选择增强目标和策略

**两层过滤**:
1. **规则预过滤** (`rules_filter`): 按指标阈值分类为 `strong` / `weak` / `discard`
   - `sharpe_min=0.5`, `fitness_min=0.3`, `turnover_max=0.9`
2. **LLM 决策** (`llm_decide`): AI 根据全局池状态选择增强计划
   - 传入 `pipeline_dir`，读取每个 Idea 的原始文件内容 (表达式+逻辑)，作为 `"idea"` 字段附在 pool_summary 中，供 LLM 做更有信息量的决策

`rules_filter` 对 `sim_summary` 中可能出现的 `None` 指标做数值兜底，避免 `None >= float` 之类比较异常中断 DECIDE。

**增强策略维度**:
- **模式 (mode)**: `single` (单个 Idea 独立增强) / `cross` (多个 Idea 交叉增强)
- **风格 (style)**: `conservative` / `balanced` / `aggressive` / `ultra-aggressive`

**默认提示词**: 内置基于 BRAIN 量化研究经验的决策提示词 (`DEFAULT_DECIDE_PROMPT`)，涵盖:
- AlphaTest 通过标准 (Sharpe≥1.25, Fitness≥1.0, Turnover 1-70%, Weight<10%, Self-corr<0.7)
- ATOM 原则 (Applicability, Trustworthiness, Originality, Magnitude)
- 增强策略选择指南

**支持自定义提示词**:
- 优先使用 `prompt_overrides.decide_system_prompt`
- 运行前会把 `{{MAX_ENHANCE_PER_ROUND}}` 渲染成当前配置值
- 若未设置 `prompt_overrides.decide_system_prompt`，则回退到旧字段 `decide_prompt`

**输出**: JSON 数组 `[{mode, style, idea_files, reason}]`

---

### 3.6 stage_enhance.py — 增强阶段

> 文件路径: `brain-orchestrator/stage_enhance.py`

**职责**: 调用 `trailSomeAlphas/enhance_template.py` 子进程对模板做增强

**增强方式**:
- **Single**: 对单个模板做参数微调、运算符替换
- **Cross**: 将多个模板交叉组合，产生融合变体

**环境变量传递**: LLM API Key/URL/Model 以及 `UNIVERSE` 通过环境变量传给子进程，确保自动增强与手动增强使用同一股票池配置

**提示词覆盖**:
- `enhance_single_system_prompt` 通过 `PIPELINE_ENHANCE_SINGLE_SYSTEM_PROMPT` 传给 `enhance_template.py`
- `enhance_cross_system_prompt` 通过 `PIPELINE_ENHANCE_CROSS_SYSTEM_PROMPT` 传给 `enhance_template.py`
- 两者都保留模板变量，实际渲染时可注入 `{{GUIDE1}}`、`{{GUIDE2}}`、`{{VECTOR_DATA_HINT}}`

**输入**: `action` dict (from DECIDE) + pipeline_dir  
**输出**: `enhanced_templates_*.json` 文件列表

---

### 3.7 stage_implement.py — 实现阶段

> 文件路径: `brain-orchestrator/stage_implement.py`

**职责**: 调用 `trailSomeAlphas/implement_idea.py` 子进程，将增强模板转化为新的 Idea

**输入**: `enhanced_templates_*.json` + `dataset_folder`  
**输出**: 新的 `idea_*.json` 文件列表 (加入池后进入下一轮 INSPECT+SIM)

---

## 4. Web API 接口

> Flask 主应用文件路径: `运行打开我.py`

Flask 主应用 (`运行打开我.py`) 提供以下 API:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/pipeline-dashboard` | GET | 流水线控制面板 HTML (`templates/pipeline_dashboard.html`) |
| `/api/pipeline/list` | GET | 列出所有流水线 (含 `decide_prompt`、`prompt_overrides`、`stop_conditions`) |
| `/api/pipeline/create` | POST | 创建并注册新流水线；创建前会校验并清洗 `prompt_overrides` 与 `stop_conditions` |
| `/api/pipeline/<id>/start` | POST | 启动流水线 |
| `/api/pipeline/<id>/stop` | POST | 停止流水线 |
| `/api/pipeline/<id>/status` | GET | 查询流水线状态 |
| `/api/pipeline/<id>/pool` | GET | 查询 Idea 池；响应前递归清洗 `NaN/Inf`，保证返回合法 JSON |
| `/api/pipeline/<id>/abort-idea` | POST | 中断指定 Idea 的回测 (body: `{idea_file}`) |
| `/api/pipeline/<id>/retry-idea` | POST | 重试指定 Idea 的回测 (body: `{idea_file}`)，重置后立即触发 `trigger_sim()` |
| `/api/pipeline/<id>/retry-inspect-idea` | POST | 重试指定 Idea 的检查；必要时携带 `validation_failures` 进入修复/重生成流程 |
| `/api/pipeline/<id>/retry-enhance-idea` | POST | 重试指定 Idea 的 single enhance |
| `/api/pipeline/<id>/update-workers` | POST | 动态调整回测并发数 (body: `{delta}`)，增加时触发 `trigger_sim()` |
| `/api/pipeline/<id>/idea-content` | GET | 返回 Idea 的 Alpha 表达式列表 (含 settings) 或原始 JSON (`?idea_file=...`) |
| `/api/pipeline/<id>/sim-detail` | GET | 返回 Idea 的逐 Alpha 回测详情: alpha_id, expression, sharpe, fitness, turnover, status (`?idea_file=...`)；数值列会将 `NaN/Inf` 归一为 `null` |
| `/api/pipeline/<id>/update-prompt` | POST | 运行期间更新决策提示词 (body: `{decide_prompt}`) |
| `/api/pipeline/<id>/update-stop-conditions` | POST | 运行期间热更新停止条件 (body: `{stop_conditions}`)；若保存后条件已满足，会立即触发停止 |
| `/api/pipeline/default-prompt` | GET | 获取内置默认决策提示词文本 |
| `/api/pipeline/prompt-templates` | GET | 获取创建前“高级设置”使用的阶段提示词模板目录 |
| `/api/pipeline/prompt-token-preview` | GET | 预览某个模板变量在运行时会展开成什么内容 |
| `/api/pipeline/<id>/log` | GET | 查询活动日志 (支持 `?n=50&phase=inspect`) |
| `/api/pipeline/<id>/stream` | GET (SSE) | 实时日志流 |

创建流水线时，BRAIN 凭据从当前登录会话自动注入，不需要用户手动填写。

---

## 5. 前端界面 (pipeline_dashboard.html)

> 文件路径: `templates/pipeline_dashboard.html`

### 创建面板
- 下拉: Region → Delay → Universe (级联加载)
- 数据集搜索: 关键词 → 列表点选
- 数据集列表显示 `coverage` 与 `date coverage`，百分比字段支持将 0~1 小数按 0%~100% 渲染
- 参数: 回测线程数、Multi Slots、每轮增强数
- LLM 配置: API Key / Base URL / Model
- `⚙ 高级设置`: 在创建前打开阶段级提示词配置弹窗
- 高级设置内维护两套状态:
  - working drafts: 当前弹窗里的临时编辑内容
  - applied drafts: 用户点击“应用”后，真正会随本次创建请求提交的覆盖
- 应用门控: 只有勾选“我已知悉仅影响当前流水线”后，“应用”按钮才可点击
- 变量提示: 模板中的 `{{TOKEN}}` 会以可点击链接展示，点击后调用 `/api/pipeline/prompt-token-preview` 查看实际展开内容
- 变量校验策略: 允许改动变量集合，不做硬拦截；前端仅提示“会丢失上下文，但通常不会导致运行时报错”
- Key 自动本地保存 (localStorage)

### 流水线卡片
- 状态徽章 (运行中/正在停止/已停止/错误)
- 当前阶段显示
- 池统计 (总数/检查完成/回测完成/已增强)
- 可展开的阶段面板
- 阶段面板内提供只读提示词预览按钮，用于查看该阶段当前生效的 system prompt / user prompt
- 卡片级“查看和修改决策提示词”入口已移除；阶段提示词修改统一在“创建前高级设置”完成
- 活动日志 (展开时才建立 SSE，折叠后立即断开)
- 启动/停止按钮

### Idea 池表格
- 列: Idea 文件 / 来源 / 检查状态 / 回测状态 / 完成数 / Sharpe均(方差) / Fitness均(方差) / 增强
- 表头支持前端排序；排序状态按流水线维度保留
- **Sharpe/Fitness 显示格式**: `均值(方差)`，如 `1.23(0.15)`
- **可点击文件名**: Idea 文件名显示为蓝色链接，点击弹出详情模态框:
  - 若已 INSPECT: 显示 Alpha 表达式列表，顶部统一展示 `delay` 和 `neutralization` 设置 (同一 Idea 内所有表达式共享)
  - 若未 INSPECT: 显示原始 Idea JSON
- **可点击完成数**: `completed/total` 中 completed > 0 时可点击，弹出逐 Alpha 回测详情表 (alpha_id, 表达式, sharpe, fitness, turnover, 状态)
- **中断按钮**: 回测状态为 `running` 时，显示红色"中断"按钮，点击调用 `/api/pipeline/<id>/abort-idea`
- **aborted 状态**: 中断后状态变为 `aborted`，显示红色斜体
- **aborted/error 完成数**: 以 `绿色 completed + 红色 failed/attempted` 显示，区分已完成与失败/中断提交数
- **重试按钮**: aborted/error 状态显示重试按钮，点击后重置为 pending 并立即触发回测

### 刷新策略
- 8秒轮询 `/api/pipeline/list`
- **Diff-based DOM 更新**: 只更新变化的元素，无闪烁
- 日志 SSE 采用按需连接，避免页面同时打开多个流水线时耗尽浏览器连接数
- 池详情采用懒加载: 第一次展开时执行 `loadPool()`，后续不跟随全局轮询自动刷新，需用户手动点击"刷新"
- SSE 实时推送日志条目

---

## 6. 持久化与恢复

### 文件持久化

| 文件 | 格式 | 写入时机 | 用途 |
|------|------|----------|------|
| `config.json` | JSON | 创建时 | 流水线配置 (不含敏感信息) |
| `state.json` | JSON | 每次状态变更 | 检查点 (iteration, phase, status) |
| `pool.json` | JSON | 每次池变更 | Idea 池完整快照 |
| `activity_log.jsonl` | JSONL | 每条日志 | 活动日志 (追加写入) |

### 恢复机制

1. `load_existing_pipelines()` 在服务启动时扫描 `pipelines/` 目录
2. 对每个含 `config.json` 的子目录，创建 `PipelineRunner` 实例
3. `PipelineState` 从 `state.json` 恢复检查点
4. **过期状态重置**: 若 `status` 为 `running` 或 `stopping` 但线程已不存在，自动重置为 `stopped`
5. `PoolManager` 从 `pool.json` 恢复 Idea 池
6. `_load_activity_log()` 从 `activity_log.jsonl` 恢复日志历史
7. 用户手动点击「启动」继续运行 (需要提供 API Key 和 BRAIN 凭据)

---

## 7. 线程模型

```
主 Flask 线程 (HTTP 请求处理)
│
├─ PipelineRunner._thread  (后台 daemon 线程，每个流水线一个)
│   │
│   ├─ 主循环: GENERATE → INSPECT+SIM(串行) → DECIDE/ENHANCE/IMPLEMENT
│   │
│   ├─ phase_simulate()  (补回测入口)
│   │   └─ ThreadPoolExecutor(max_workers=sim_concurrent)
│   │       ├─ Worker-1: simulate_idea(idea_A, concurrency=1)
│   │       ├─ Worker-2: simulate_idea(idea_B, concurrency=1)
│   │       └─ Worker-N: ...
│   │       每个 Worker → BatchSimulator → BRAIN multi-sim API
│   │
│   └─ _decide_thread  (后台 DECIDE daemon 线程)
│       └─ 独立 BRAIN 会话 (_decide_session)
│           → DECIDE → ENHANCE → IMPLEMENT
│
├─ SSE 连接 (subscribe/unsubscribe, queue.Queue per client)
│
├─ 全局 Worker 额度: GLOBAL_WORKER_LIMIT=8
│   └─ global_worker_usage(): sum(running_pipelines.sim_concurrent) ≤ 8
│
└─ 锁:
    PipelineState._lock   — 每个流水线的状态互斥
    PoolManager._lock     — Idea 池 CRUD 互斥
    _log_file_lock        — 日志文件追加写互斥
    _registry_lock        — 流水线注册表互斥
```

---

## 8. 数据流图

```
┌──────────────────────────────────────────────────────────┐
│                    GENERATE (首次)                        │
│  run_pipeline.py → ideas/idea_*.json                     │
└──────────────────┬───────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────┐
│    逐 Idea 处理 (INSPECT → SIM, 并行触发 DECIDE)         │
│                                                          │
│  ┌─ INSPECT ─────────────────────────────────────────┐   │
│  │  idea_*.json                                      │   │
│  │  → parse_idea_file → fetch_sim_options            │   │
│  │  → LLM 选参 → validator → build_alpha_list        │   │
│  │  → inspect/<stem>/alpha_list.json                 │   │
│  └───────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  ┌─ SIMULATE ────────────────────────────────────────┐   │
│  │  alpha_list.json                                  │   │
│  │  → BatchSimulator (multi-sim API)                 │   │
│  │  → sim/<stem>_simulation_status.csv               │   │
│  │  → pool.update(sim_summary)                       │   │
│  └───────────────────────────┬───────────────────────┘   │
│                              ▼                           │
│  ┌─ 后台 DECIDE (自动触发) ──────────────────────────┐   │
│  │  pool.candidates_for_enhance()                    │   │
│  │  → rules_filter (strong/weak/discard)             │   │
│  │  → LLM 决策 (mode/style/idea_files)              │   │
│  │  │                                                │   │
│  │  ├─ ENHANCE: enhance_template.py                  │   │
│  │  │  → enhanced_templates_*.json                   │   │
│  │  │                                                │   │
│  │  └─ IMPLEMENT: implement_idea.py                  │   │
│  │     → new idea_*.json → 加入池 → 下轮 INSPECT     │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 9. 错误处理与恢复

| 场景 | 处理方式 |
|------|----------|
| INSPECT 失败 | 标记 `inspect_status="error"`, 跳过该 Idea 的 SIM |
| retry-inspect 遇到纯语法失效 | 若 `validation_failures` 存在且无有效表达式，则进入 LLM 修复/重生成路径，而不是机械重放原始 inspect |
| SIMULATE 失败 | 标记 `sim_status="error"`, 继续下一个 Idea |
| SIMULATE 中断 | 用户点击"中断" → `abort_idea()` → `cancel_check` 回调传播至 BatchSimulator 各轮询循环 → 标记 `sim_status="aborted"` |
| DECIDE/ENHANCE/IMPLEMENT 失败 | 后台线程捕获异常, 记录日志, 不影响主循环 |
| 主循环 DECIDE 异常 | 主循环显式捕获并记录日志，避免线程静默退出后状态残留为 `running` |
| BRAIN 会话过期 | 每轮迭代开始时 `check_session_and_relogin`, 失败则重建 |
| 所有 INSPECT 失败 | 60秒冷却后重置为 pending 重试 |
| 所有 SIM 失败 | 60秒冷却后重置为 pending 重试 |
| 无新 Idea 产出 | 60秒等待后进入下一轮 |
| 停止信号 | `_stop_event.set()`, 循环中多处检查, 优雅退出 |

---

## 10. 外部依赖

| 组件 | 相对路径 | 用途 |
|------|----------|------|
| `ace_lib.py` | `brain-orchestrator/scripts/vendor/ace_lib.py` | BRAIN API 会话管理、认证、API 调用 |
| `batch_simulator.py` | `brain-orchestrator/scripts/vendor/batch_simulator.py` | 批量 Alpha 回测引擎 (含 `cancel_check` 中断支持) |
| `enhance_template.py` | `trailSomeAlphas/enhance_template.py` | 模板增强 (single/cross) |
| `implement_idea.py` | `trailSomeAlphas/scripts/implement_idea.py` | 增强模板 → 新 Idea |
| `run_pipeline.py` | `trailSomeAlphas/run_pipeline.py` | GENERATE 阶段：LLM 生成初始 Idea |
| Moonshot/Kimi API | 外部 | LLM 推理 (temperature=1) |
| BRAIN API | 外部 | 回测、数据集查询、提交 |

---

## 11. LLM 使用约定

- **模型**: kimi-k2.5 (默认)，兼容所有 OpenAI 格式 API
- **Temperature**: 始终为 **1** (不可更改，确保创造性)
- **使用场景**:
  - GENERATE: 生成 Alpha Idea (表达式 + 经济学逻辑)
  - INSPECT: 选择最佳回测参数组合
  - DECIDE: 评估回测结果，选择增强策略
  - ENHANCE: 模板增强 (在子进程中)

---

## 12. 回测中断机制 (Abort)

### 中断链路

```
前端 "中断" 按钮
  → POST /api/pipeline/<pid>/abort-idea  {idea_file}
    → PipelineRunner.abort_idea(idea_file)
      → _abort_ideas.add(idea_file)        # 线程安全集合
      → pool.update(sim_status="aborted")  # 更新池状态
      → log_activity(warning)
        ↓
    cancel_fn = lambda: _is_idea_aborted(idea_file)
      → 传入 simulate_idea(cancel_check=cancel_fn)
        → BatchSimulator(cancel_check=cancel_fn)
          → 父轮询循环: 每次迭代前检查
          → 子轮询循环: 每次 sleep 周期间检查
          → run() 线程池: future 迭代间检查
```

### 关键修复: Retry-After 头部处理

`batch_simulator.py` 子轮询循环中，BRAIN API 有时在已完成的 200 响应上也返回 `Retry-After` 头部。旧代码在检测到 `Retry-After` 头部后直接 `continue` 跳过响应解析，导致已完成的回测永远不被识别，触发 30 分钟超时。

**修复**: 先解析响应 JSON 获取 `status` 字段，仅在状态非终态 (COMPLETED/ERROR/FAIL) 时才根据 `Retry-After` 值 sleep。

---

## 13. 提示词体系

当前系统同时存在两套提示词入口，职责不同:

### 13.1 创建前高级设置

创建表单中的“⚙ 高级设置”用于配置本次新建流水线的阶段级 `prompt_overrides`:

- 前端启动时通过 `/api/pipeline/prompt-templates` 拉取阶段模板目录
- 支持 6 个阶段级覆盖 key:
  - `generate_system_prompt`
  - `inspect_settings_system_prompt`
  - `inspect_repair_system_prompt`
  - `decide_system_prompt`
  - `enhance_single_system_prompt`
  - `enhance_cross_system_prompt`
- 弹窗默认直接可编辑，不再区分“编辑/停止编辑”模式
- 用户在弹窗中的修改先写入 working drafts；只有点击“应用”后才进入 applied drafts，并随 `/api/pipeline/create` 一起发送
- applied drafts 只影响当前这一次创建，不会修改系统默认模板

### 13.2 变量预览

高级设置中的模板变量以可点击链接显示:

- 点击变量后，前端调用 `/api/pipeline/prompt-token-preview`
- 后端按 `section_key + token + data_type + max_enhance_per_round` 生成预览内容
- 典型变量包括:
  - `{{FEATURE_ENGINEERING_SKILL_MD}}`
  - `{{FEATURE_IMPLEMENTATION_SKILL_MD}}`
  - `{{ALLOWED_OPERATORS_JSON}}`
  - `{{ALLOWED_PLACEHOLDERS_JSON}}`
  - `{{GUIDE1}}`
  - `{{GUIDE2}}`
  - `{{VECTOR_DATA_HINT}}`
  - `{{VECTOR_OPERATORS_LINE}}`
  - `{{MAX_ENHANCE_PER_ROUND}}`

### 13.3 运行中只读预览

流水线卡片不再提供统一的可编辑提示词入口；取而代之的是阶段面板里的只读预览:

- 预览展示的是该阶段“当前生效”的内容，不是默认模板目录
- 对 INSPECT 选参阶段，当前生效的 system prompt 会显示出来，但 `neutralization/universe/decay` 候选本身仍来自 user prompt `candidates`
- 对 DECIDE 阶段，若存在 `prompt_overrides.decide_system_prompt`，其优先级高于旧字段 `decide_prompt`

### 13.4 旧版运行期决策提示词编辑

`/api/pipeline/<id>/update-prompt` 与 `/api/pipeline/default-prompt` 仍保留，用于兼容旧版只修改 `decide_prompt` 的流程；但新的主路径已经转向创建前 `prompt_overrides`

### 13.5 停止条件

创建表单中的“🛑 停止条件”与卡片操作区中的同名按钮，共用一套 stop condition 配置模型:

- 默认全部留空 / 关闭，表示无界，不会自动停止
- 创建前设置会随 `/api/pipeline/create` 一起落入 `config.json`
- 运行中修改通过 `/api/pipeline/<id>/update-stop-conditions` 热更新到 `runner.config`，并立即重新评估一次
- runner 会在 GENERATE 完成后、每轮 SIMULATE 后、每轮 DECIDE/ENHANCE/IMPLEMENT 后统一执行 stop check，而不是在各阶段内部各写一套中断逻辑

当前 stop check 指标来源:

- `max_pool_ideas`: 来自 `PoolManager.size()`
- `max_iterations`: 来自 `state.iteration`
- `max_alpha_submitted` / `max_sim_completed`: 来自各 Idea 的 `sim_csv` 最新行与 `sim_summary`
- `sharpe_target_count`: 逐个 `sim_csv` 统计 `status=COMPLETED` 且 `sharpe >= min_sharpe` 的结果数
- `diminishing_returns`: 按 `origin=enhance_round_N` 聚合最近几轮增强产生的 completed/qualified 比率，与历史轮次基线比较

---

## 14. 前端 JS 安全处理

### Windows 路径反斜杠转义

`idea_file` 字段包含 Windows 反斜杠路径 (如 `implement\round_17\analyst40_USA_1_idea_xxx.json`)。在动态生成 `onclick` 处理器时，`\r`, `\n`, `\t`, `\f` 等序列会被 JavaScript 解释为控制字符，导致传递到后端的字符串损坏。

**解决方案**:
- `escJsStr(s)` — 转义反斜杠 (`\` → `\\`) 和单引号 (`'` → `\'`)，用于 onclick 内联 JS 字符串
- `escHtml(s)` — 仅用于 HTML 属性值 (如 `title`) 的转义
- 文件名提取: `.split(/[/\\]/).pop()` 同时处理正斜杠和反斜杠

---

## 15. 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v1.0 | 2026-03-07 | 初始稳定版: 6 阶段流水线、并行 DECIDE、中断/重试、提示词查看与编辑、CSV 路径去冲突、过期状态自动重置、Windows 路径转义修复 |
| v1.0.1 | 2026-03-07 | **核心修复: ThreadPoolExecutor 跨 Idea 并行回测**。`phase_simulate()` 从串行 for 循环重写为 `ThreadPoolExecutor(max_workers=sim_concurrent)` 并行调度；移除向 `simulate_idea()` 误传 `sim_concurrent` 参数的 bug；全局 Worker 额度限制 (GLOBAL_WORKER_LIMIT=8) + 前端动态 +/- 调整 |
| v1.0.2 | 2026-03-07 | **并行 INSPECT + 交互增强 + Bug 修复**: ①INSPECT 阶段改为 `ThreadPoolExecutor(max_workers=5)` 并行 ②优雅 Worker 缩减 (`get_worker_limit` 回调) ③DECIDE LLM 接收 Idea 原始内容 ④stopping/stopped/running 三态按钮 ⑤Pool 表格文件名可点击查看表达式 (delay+neutralization 统一展示) ⑥完成数可点击查看逐 Alpha 详情 ⑦`retry_idea()` 即时触发 `trigger_sim()` |
| v1.0.3 | 2026-03-08 | **稳定性与可观测性增强**: ①日志 SSE 改为展开时按需连接，池详情改为首次展开懒加载 + 手动刷新 ②Pool 表头支持排序，aborted/error 完成数区分 completed 与 failed/attempted ③数据集列表新增 coverage / date coverage 展示并修正小数百分比渲染 ④`/pool` 与 `/sim-detail` 对 `NaN/Inf` 做 JSON 安全清洗 ⑤DECIDE 对 `None` 指标做数值兜底，主循环 DECIDE 异常显式记录日志 ⑥ENHANCE 显式透传 `UNIVERSE` ⑦`retry-inspect-idea` 支持基于 `validation_failures` 的 LLM 修复/重生成，并提高修复超时 |
| v1.0.4 | 2026-03-08 | **阶段级提示词覆盖与高级设置**: ①新增 `prompt_overrides` 配置模型，覆盖 GENERATE / INSPECT / DECIDE / ENHANCE 阶段 system prompt ②创建页新增“高级设置”弹窗，采用 working draft / applied draft 双层状态与全局确认门控 ③新增 `/api/pipeline/prompt-templates` 与 `/api/pipeline/prompt-token-preview` ④卡片级旧提示词编辑入口下线，改为阶段只读预览 ⑤文档明确 INSPECT 选参候选通过 user prompt `candidates` 传入，而非 system prompt 变量注入 |
| v1.0.5 | 2026-03-08 | **流水线停止条件**: ①新增 `stop_conditions` 配置模型，支持 Sharpe 目标数、池大小、回测提交量、回测完成量、迭代上限、增强收益递减 ②创建页新增“停止条件”弹窗，默认全部关闭 ③卡片级新增运行中热更新入口 ④runner 在统一 checkpoint 执行 stop check，并记录 `stop_reason` / `stop_source` |
