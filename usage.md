# 使用说明（usage.md）

本文档面向本仓库的本地 Flask Web APP，聚焦“如何在网页上使用各功能 + 每个功能的目的”。不包含 bug 修复与代码改动建议。

---

## 1. 启动与访问

1. 在 `APP/` 目录启动：
   - Windows：双击 `run_app.bat`（或在终端运行它）
   - 或直接运行：`python 运行打开我.py`
2. 浏览器打开：`http://localhost:5000/`

> 说明：项目内的 `README.md` 可能仍写 `python app.py`，但本工作区实际入口脚本是 `运行打开我.py`。

---

## 2. 几个重要概念（你会频繁用到）

- **模板占位符**：在表达式里用形如 `<xxx/>` 的占位符，后续通过弹窗为每个模板配置一组可替换的值。
- **两种生成方式**：
  - `full_iteration`：枚举所有组合
  - `random_iteration`：在组合空间中抽样
- **Settings（回测设置）追加**：在“Results”页点 `Append Expression with Settings`，生成可供回测器使用的 JSON：`expressions_with_settings.json`。
- **浏览器存储**：
  - BRAIN 的 `session_id` 会存到浏览器 `localStorage`（键名类似 `brain_session_id`）
  - Deepseek/Kimi 的 API Key 等通常存到 `sessionStorage`
  - 关闭标签页/浏览器后，`sessionStorage` 可能会丢失，需要重新填。

---

## 3. 快速上手（最常用的一条完整链路）

目标：从“模板表达式”生成一批可回测的 Alpha 表达式，并用 Web 回测器批量回测。

1. 进入首页（`/`），在 **Expression Editor** 里编辑表达式（可包含 `<xxx/>` 模板）。
2. 右侧 **Detected Templates** 会自动识别模板；点击模板会弹出配置窗口：
   - 普通模板：在弹窗里用英文逗号分隔输入候选值
   - 若出现 `Choose from BRAIN`：可从 BRAIN 拉取 Operators 或 DataFields（需要先连接 BRAIN）
3. 点击右侧 `Next: Decode Templates →` 进入 **Decode Templates**：
   - 点 `full_iteration` 生成全量
   - 或点 `random_iteration` 并设置 `Count`
4. 进入 **Results**：
   - 点 `Download All Expression in txt`：下载纯文本表达式列表
   - 点 `Append Expression with Settings`：填写/选择 settings 后下载 `expressions_with_settings.json`
5. 回到首页点 `🚀 打开回测器`，在弹窗选择 **Web 界面**（会打开 `/simulator`）：
   - 上传 `expressions_with_settings.json`
   - 填入 BRAIN 账号密码
   - 点 `🔗 Test Connection`（可选但建议）
   - 点 `🚀 Start Simulation` 开始批量回测
6. 在右侧日志区查看运行进度；必要时可 `⏹️ Stop`。

---

## 4. 首页（`/`）：模板解码器

### 4.1 顶部快捷入口（目的与用法）

- `Connect to BRAIN`
  - 功能：让模板配置时能“从 BRAIN 选择 Operators/DataFields”，并把 operators 缓存在浏览器里供其它页面使用。
  - 用法：点击后弹出登录框，输入 `Username / Password`，点 `Connect`。
  - 若触发额外验证：页面会出现 `Complete Authentication`（或类似）按钮/提示，按提示在新窗口完成验证后回到页面。

- `🚀 打开回测器`
  - 功能：批量回测表达式。
  - 用法：点击后会弹窗让你选择：
    - **命令行界面**：启动 `simulator/simulator_wqb.py`（在新终端窗口运行）
    - **Web 界面**：打开 `/simulator`（推荐）

- `📤 交个Alpha`
  - 功能：打开提交相关的命令行工具。
  - 用法：点击后会在新终端窗口运行 `simulator/alpha_submitter.py`。

- `🚀 Open Simulator_hk`
  - 功能：打开港股相关的命令行回测工具。
  - 用法：点击后会在新终端窗口运行 `hkSimulator/autosimulator.py`。

- `七十二变`
  - 功能：基于“种子 Alpha”自动生成大量变体（模板和/或表达式）。
  - 用法：点击后弹窗让你选择：
    - **命令行界面**：启动 `Tranformer/Transformer.py`（新终端窗口）
    - **Web 界面**：打开 `/transformer-web`（推荐）

- `🌉 缘分一道桥`
  - 功能：把一批 Alpha 跨 Region/Universe/Delay 寻找可用字段组合，并生成待回测表达式。
  - 用法：点击进入 `/alpha_inspector`。

- `为已有Alpha推荐OP`：进入 `/inspiration-house/`（Operator 建议/打分）。
- `论文分析`：进入 `/paper-analysis/`（上传论文，Deepseek 分析关键词/摘要/公式）。
- `从数据字段到Alpha`：进入 `/feature-engineering/`（多步 DataField 探索建议）。

### 4.2 模板空间（“模板管理/导入导出/接 72 变”）

在首页的“模板空间”里，你会看到：

- 示例模板按钮：如 `Vector数据处理模板`、`单字段深度处理` 等。
- 用户自建模板：通过 `Save Current Template` 保存当前编辑器内容。
- 72 变模板：通过“加载72变生成的模板”导入。

可用按钮：
- `Save Current Template`：保存当前编辑器内容到本地存储。
- `Overwrite Existing`：覆盖已存在的同名模板。

### 4.3 找灵感 (Alpha Inspiration Master)

位于编辑器工具栏的 `💡 找灵感` 按钮，提供基于 LLM (如 Kimi/Moonshot) 的 Alpha 灵感生成功能。

**功能流程：**
1. **前置条件**：需先登录 BRAIN（点击 `Connect to BRAIN`）。
2. **打开工具**：点击编辑器上方的 `💡 找灵感` 按钮，打开配置弹窗。
3. **配置 LLM**：
   - 填入 Base URL (默认 Moonshot API)
   - 填入 API Key
   - 选择模型 (如 `kimi-k2.5`)
4. **选择数据**：
   - 选择 Region / Universe / Delay
   - 搜索并选择一个 Dataset (如 `analyst10`)
   - 系统会自动拉取该 Dataset 的字段信息和 BRAIN 的 Operators。
5. **生成灵感**：
   - 点击 `Generate Alpha Templates`。
   - LLM 会根据字段含义和运算符文档，推荐一批 Alpha 模板。
6. **使用结果**：
   - 生成的模板可以直接复制到编辑器中使用，或下载保存。

---

## 5. 进阶功能页
- `只展示用户自建模板`：切换模板按钮区的显示范围。
- `📤 导出用户自建模板`：导出自建模板为 JSON 文件。
- `📥 导入用户自建模板`：导入之前导出的 JSON。
- `🤖 加载72变生成的模板`：选择 72 变下载的 `Alpha_candidates.json`（或类似结构文件），把“模板候选”加入模板空间。
- `📄 载入72变生成的表达式`：导入“表达式列表 JSON”。
  - 常见来源：72 变 Web 下载的 `Alpha_generated_expressions_success.json`
  - 页面也支持载入“JSON 数组（每项为字符串表达式）”的文件

### 4.4 Expression Editor（编辑器页）

功能：编写/粘贴带模板的表达式，并进行基础语法检查与模板检测。

常用操作：

- `Clear`：清空编辑器。
- `Save Current Template`：把当前编辑器内容保存为“用户自建模板”。
- `Overwrite Existing`：覆盖已有模板（用于更新同名模板）。

右侧信息栏：

- `Detected Templates`：自动列出识别到的 `<xxx/>` 模板。
- `Grammar Rules`：展示此编辑器的语法规则（如分号、注释等）。

### 4.5 Decode Templates（解码页）

功能：把模板的候选值做组合，生成最终表达式列表。

- `full_iteration`：生成所有组合。
- `random_iteration`：抽样生成；右侧 `Count` 输入抽样数量。

### 4.6 Results（结果页）

功能：查看/下载生成的表达式，并将表达式与 settings 组合成回测 JSON。

- `Download All Expression in txt`：下载表达式纯文本。
- `Append Expression with Settings`：打开 settings 配置表。
  - 常见字段：`region / universe / delay / decay / neutralization ...`
  - 配置完成后会下载：`expressions_with_settings.json`

---

## 5. Web 回测器（`/simulator`）

功能：把 `expressions_with_settings.json` 批量发送到 BRAIN 做 simulation，并在页面查看日志。

### 5.1 需要准备什么

- 文件：`expressions_with_settings.json`（通常来自首页 Results 页的 settings 追加功能）
- 账号：WorldQuant BRAIN 用户名密码

### 5.2 页面字段与按钮

- `📁 Expressions JSON File`：上传 JSON（提示：`Select expressions_with_settings.json file`）
- `👤 BRAIN Username / 🔒 BRAIN Password`
- `🎯 Starting Position`：从第 N 条表达式开始（0-based）
- `⚡ Concurrent Simulations`：并发回测数量
- `🔀 Random Shuffle`：随机打乱表达式顺序
- `🎛️ Multi-Simulation Mode`：多表达式合并回测槽位（展开后设置 `📊 Alphas per Slot`）
- `🔗 Test Connection`：测试登录/连接
- `🚀 Start Simulation`：开始
- `⏹️ Stop`：停止

### 5.3 日志查看

右侧 `📊 Simulation Logs & Status`：

- 可用 `📁 Select Log File` 下拉选择历史日志
- `🔄 Refresh` 刷新日志列表
- 中央日志窗口持续输出运行信息

---

## 6. 七十二变（Transformer）Web（`/transformer-web`）

功能：输入“种子 Alpha ID”，结合 LLM + BRAIN 信息，生成模板/表达式的变体，并提供下载。

### 6.1 基本步骤

1. 在 `Configuration` 区填写 LLM 参数：
   - `LLM Model Name`（默认 `kimi-k2.5`）
   - `LLM API Key`
   - `LLM Base URL`（默认 `https://api.moonshot.cn/v1`）
2. 点击 `Test LLM Connection`，显示成功后继续。
3. 填写 BRAIN 账号：`BRAIN Username / BRAIN Password`，点 `Login & Fetch Options`。
4. 填写/调整 `Template Summary`（可点 `📂 Load from File` 导入 txt/md）。
5. 填 `Alpha ID`，设置 `Datafield Top N`。
6. 可选：选择目标 `region / delay / universe`，以及“目标数据类别（可多选）”。
   - **Data Type**：默认为 `MATRIX`。若选择 `VECTOR`，会弹出警告提示，需确认原型 Alpha 正确使用了 vector operator。
7. 点 `Run Transformer`，右侧 `Output Log` 会滚动输出。
8. 生成结束后，页面出现下载区：
   - `Download Alpha_candidates.json`：模板文件（可回首页“加载72变生成的模板”再精细化改）
   - `Download Alpha_generated_expressions_success.json`：可用表达式列表（可回首页“载入72变生成的表达式”或进入回测器）
   - `Download Alpha_generated_expressions_error.json`：被过滤/报错的表达式（用于排查模板质量）

---

## 7. 缘分一道桥（`/alpha_inspector`）

功能：批量获取 Alpha（按日期范围或指定 ID），分析字段在不同 Region/Universe/Delay 的可用性，生成新的表达式，并提供“下载待回测/排队回测”。

### 7.1 使用步骤

1. 进入页面后先在“登录 BRAIN”区输入用户名（邮箱）与密码，点 `登录`。
2. 在“选择模式”里选择：
   - `按日期范围`：填开始/结束日期（页面提示不建议超过 30 天）
   - `指定 Alpha ID`：在文本框里输入多个 ID（逗号/空格/换行分隔）
3. 点击 `获取 Alpha 并分析`。
4. 结果区会展示 Alpha 列表（可展开查看详情）。
5. 需要批量回测时：
   - 点 `下载所有待回测Alpha`：把待回测表达式下载到本地
   - 或点 `一键全部排队回测`：在本页串行排队回测（页面提示：中途关闭页面会中断队列）

---

## 8. 为已有Alpha推荐OP（`/inspiration-house/`）

功能：基于你的“研究目标 + 当前表达式”，对大量 operator 做 AI 评价/打分，给出“加哪些 operator 更可能改进目标”的建议。

### 8.1 先配置模型

- 在 `API Configuration`：
  - `AI Model Provider`：Deepseek / Kimi
  - `API Key`
  - `Model Name`（示例：`deepseek-chat` 或 `kimi-k2.5`）
  - `Worker Configuration`（`batchSize`）：批处理大小
- 点 `Test & Save Configuration`

### 8.2 设置目标与表达式

- `🎯 Quant Research Target`：点 `Edit Target`，填写你的目标（例如降低换手、提高 Sharpe、降低回撤等）
- `📝 Current Expression`：
  - 输入表达式
  - 或点 `Load from BRAIN`（从已连接的 BRAIN 缓存/接口获取）

### 8.3 开始评价与导出

- 点 `Start AI Evaluation`
- 可用筛选：Min/Max Score、只看高分/中分/低分
- `Export Results` 导出结果

> 建议：先在首页 `Connect to BRAIN`，让 operator 列表更完整。

---

## 9. 论文分析（`/paper-analysis/`）

功能：上传论文文件，用 Deepseek 做关键词/摘要/公式（页面里称 Formulas）提取与整理。

使用步骤：

1. 在 `Deepseek API Configuration` 输入 `API Key`，点 `Save API Key`（会测试连接）。
2. 在 `Upload Paper` 上传文件（支持：PDF/TXT/DOC/DOCX/RTF/LaTeX/Markdown）。
3. 在 `Analysis Options` 勾选需要的内容：
   - `Extract Mathematical Formulas`
   - `Extract Keywords`
   - `Generate Summary`
4. 点 `Analyze Paper`。
5. 在结果区切换 `Keywords / Summary / Formulas` 查看。
6. 点 `Export Results` 导出。

---

## 10. 从数据字段到Alpha（Feature Engineering）（`/feature-engineering/`）

功能：以“多步 pipeline”的方式，让 AI 给出 DataField 探索/加工/组合的推荐方案；支持编辑 system prompt、导出 pipeline。

使用步骤：

1. 在 `API Configuration` 配置 Deepseek/Kimi：Provider、API Key、Model Name，点 `Test & Save Configuration`。
2. 在 `Start New Feature Engineering Pipeline`：
   - 点 `Load Question Template` 生成模板
   - 在 `Question Template` 中填入你当前 datafield、描述、EDA 观察等
   - 如需：点 `Edit System Prompt` 调整提示词（也可 `Load Default Prompt`）
3. 点 `Get AI Recommendations`。
4. 在 `AI Recommendations` 区查看推荐选项：
   - `Clear & Start Over`：清空并重新开始
   - `Export Pipeline`：导出 pipeline

---

## 11. 外部账号与 Key：去哪里申请、在哪填、怎么验证

> 网址/入口可能随平台更新而变化；若打不开，以平台官网的“API / 开发者 / Keys”入口为准。

### 11.1 WorldQuant BRAIN（账号）

- 去哪申请：WorldQuant BRAIN 官网注册账号。
- 在哪填：
  - 首页 `Connect to BRAIN`
  - Web 回测器 `/simulator`
  - 72 变 `/transformer-web`
  - 缘分一道桥 `/alpha_inspector`
- 怎么验证：各页面都有登录/连接测试流程（如 `Connect`、`Test Connection`、`Login & Fetch Options`）。

### 11.2 Deepseek（API Key）

- 去哪申请：Deepseek 开放平台/开发者平台创建 API Key。
- 在哪填：
  - `/paper-analysis/`：`API Key` → `Save API Key`
  - `/inspiration-house/`：Provider 选 `Deepseek`，填 `API Key` → `Test & Save Configuration`
  - `/feature-engineering/`：Provider 选 `Deepseek`，填 `API Key` → `Test & Save Configuration`
- 怎么验证：上述页面的测试按钮会调用后端 `.../api/test-deepseek`。

### 11.3 Kimi / Moonshot（API Key）

- 去哪申请：Moonshot/Kimi 开放平台创建 API Key。
- 在哪填：
  - `/inspiration-house/`：Provider 选 `Kimi`
  - `/feature-engineering/`：Provider 选 `Kimi`
  - `/transformer-web`：`LLM API Key` + `LLM Base URL`（默认 `https://api.moonshot.cn/v1`）
- 怎么验证：
  - `/inspiration-house/`、`/feature-engineering/`：`Test & Save Configuration`
  - `/transformer-web`：`Test LLM Connection`

---

## 12. 常见使用建议（不涉及修复，仅帮助你更顺畅）

- 如果某页面提示缺少 operators/datafields：优先回首页 `Connect to BRAIN` 再刷新页面。
- 72 变生成后的三类文件，建议按用途回流：
  - `Alpha_candidates.json` → 首页“加载72变生成的模板” → 再用解码器精细化
  - `Alpha_generated_expressions_success.json` → 首页“载入72变生成的表达式”或直接去回测器
  - `Alpha_generated_expressions_error.json` → 用于检查模板/提示词是否存在系统性错误
- API Key / Token 请勿写入仓库或公开分享；尽量只在本地浏览器会话中使用。
