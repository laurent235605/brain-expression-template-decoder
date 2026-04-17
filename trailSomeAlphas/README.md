# trailSomeAlphas

This folder is the runnable pipeline hub for:
- idea generation (`run_pipeline.py`)
- template enhancement (`enhance_template.py`)
- template implementation to expressions (`implement_idea.py` via scripts)

It bundles `brain-data-feature-engineering` and `brain-feature-implementation` so enhancement and implementation can run end-to-end.

## Major Features

### 1) Pipeline generation (`run_pipeline.py`)
- Generate idea report markdown from dataset metadata
- Parse implementation examples and produce expression candidates
- Save final expressions under dataset folder

### 2) Template enhancement (`enhance_template.py`)
- **Single mode**: enhance one idea JSON
- **Cross mode**: enhance multiple idea JSONs together (`IDEA_JSON_LIST`)
- In both modes, enhancement is followed by implement + merge + dedup + validator filtering

### 3) Cross enhancement styles
- `conservative`
- `balanced` (default)
- `aggressive`
- `ultra-aggressive`

## Setup

1) Configure BRAIN credentials (for dataset fetch/rebuild when needed)
- `skills/brain-feature-implementation/config.json`

2) Set Moonshot API key (recommended via env)
- PowerShell:
  - `$Env:MOONSHOT_API_KEY = "<your_api_key>"`

Optional:
- `MOONSHOT_BASE_URL` (default: `https://api.moonshot.cn/v1`)
- `MOONSHOT_MODEL` (default from script)

## Run

From this folder (`untracked/APP/trailSomeAlphas`):

### A. Pipeline mode
- Generate ideas + implement expressions:
  - `python run_pipeline.py --data-category analyst --region USA --delay 1 --universe TOP3000`
- Use existing ideas markdown:
  - `python run_pipeline.py --data-category analyst --region USA --delay 1 --ideas-file <path_to_ideas.md>`

### B. Enhance mode (script)

#### Single input
- Set:
  - `IDEA_JSON=<path_to_idea_json>`
- Run:
  - `python enhance_template.py`

#### Cross input
- Set:
  - `IDEA_JSON_LIST=["<idea1.json>", "<idea2.json>", "..."]`
  - `CROSS_PROMPT_STYLE=balanced` (optional)
- Run:
  - `python enhance_template.py`

## Validation Rules (implemented in flow)

- Input JSON must contain `template` and `idea`
- Cross filenames must parse as `<dataset>_<region>_<delay>_idea_<ts>.json`
- Cross inputs must share identical `(dataset, region, delay)`
- `DATA_TYPE` accepts only `MATRIX` or `VECTOR` (invalid values fallback to `MATRIX`)
- Dataset CSV is ensured/readable before implementation

## Output

### Pipeline outputs
- Ideas report:
  - `skills/brain-data-feature-engineering/output_report/{region}_delay{delay}_{datasetId}_ideas.md`
- Final expressions:
  - `skills/brain-feature-implementation/data/{datasetId}_{region}_delay{delay}/final_expressions.json`

### Enhance outputs
- Enhanced templates:
  - `enhanced_templates_<timestamp>.json`
- Final expressions from enhanced templates:
  - `enhanced_final_expressions_<timestamp>.json`

Both are written into the same folder as the primary input idea JSON.

## Web Integration Notes

Routes are hosted by `APP/运行打开我.py`:
- Single enhance: `/api/inspiration/enhance-template`
- Cross enhance: `/api/inspiration/cross-enhance-template`
- Stream: `/api/inspiration/stream-enhance/<task_id>`
- Download: `/api/inspiration/download-enhance/<task_id>`

Current behavior:
- Cross download is flat and includes:
  - selected original input JSONs
  - `enhanced_templates_*.json`
  - `enhanced_final_expressions_*.json`
- Non-cross download keeps folder structure
- Progress UI uses task-level completion semantics (`done` event)

## Cross 手动输入（Web）

Cross 模式现在支持不上传文件，直接手动输入。

入口：
- 点击 `多源模板增强`
- 在“选择数据类型”弹窗里点击 `手动输入`

必填项：
- `datasetId`
- `region`
- `delay`
- 第一组：`template`（必填）+ `idea`
- 第二组：`template2`（必填）+ `idea2`

约束与校验：
- cross 手动模式至少需要 2 组 template（`template` 和 `template2`）
- `datasetId` 必须同时包含字母和数字（例如 `fundamental28`）
- `region` 自动转大写，`datasetId` 自动转小写
- `delay` 必须是整数（0~10）

后端处理方式：
- 会按 `<dataset>_<region>_<delay>_idea_<ts>.json` 规则生成多份临时 idea JSON
- 自动组装为 `IDEA_JSON_LIST`，并走与文件上传 cross 相同的增强/implement/过滤流程
