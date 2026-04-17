import requests
import json
import sys
import asyncio
import openai
import re
from typing import Optional, Union # Added this import
try:
    from .validator_hooks import is_valid_template_expr, has_empty_datafield_candidates
except Exception:
    # Fallback for direct script execution
    try:
        from validator_hooks import is_valid_template_expr, has_empty_datafield_candidates
    except Exception:
        is_valid_template_expr = None
        has_empty_datafield_candidates = None

# --- Validation wrappers to integrate into the pipeline ---
def _filter_valid_templates(
    proposed_templates: dict,
    operators_meta,
    brain_session,
    settings: dict,
    parse_alpha_code_func,
):
    """Return dict of only templates that pass validation.

    Safe no-op if validation helpers are unavailable.
    """
    if not is_valid_template_expr or not parse_alpha_code_func:
        return proposed_templates
    filtered = {}
    for template_expr, template_expl in proposed_templates.items():
        try:
            if is_valid_template_expr(
                template_expr,
                operators_meta,
                brain_session,
                settings,
                parse_alpha_code_func,
            ):
                filtered[template_expr] = template_expl
        except Exception:
            # Be conservative: drop on exceptions
            continue
    return filtered


def _should_skip_due_to_empty_candidates(populated_info: dict) -> bool:
    """True if any data_field placeholder has zero candidates.

    Safe no-op fallback when helper is missing.
    """
    if not has_empty_datafield_candidates:
        return False
    try:
        return has_empty_datafield_candidates(populated_info)
    except Exception:
        return False
import logging
import pandas as pd
import os
from pathlib import Path
from urllib.parse import urljoin
import time
import threading
import itertools
import getpass
import io
import validator as val
from ace_lib import get_instrument_type_region_delay
# Force stdout/stderr to use utf-8 on Windows to avoid UnicodeEncodeError
if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# 这些变量将在交互式输入中设置
LLM_model_name = None
LLM_API_KEY = None
llm_base_url = None
username = None
password = None
DATA_CATEGORIES = None


template_summary = """# BRAIN论坛Alpha模板精华总结

本文档旨在系统性地整理和总结优秀Alpha模板,它是一种可复用的标准化框架性表达式，它承载着特定的经济逻辑，并预留出若干 “配置项”（包括数据字段、运算符、分组方式、衰减规则、中性化方案等），用于生成多个候选阿尔法因子。其典型流程为：数据清洗（数据回填、缩尾处理）→ 跨时间或跨标的维度进行转换 / 对比 → 排序 / 中性化处理 →（可选步骤）衰减调整 / 换手率优化。这种模板模式能够推动系统化的因子挖掘、复用与多元化配置，同时确保每一个因子都具备清晰可追溯的经济逻辑支撑。
以下每个模板都附有其核心思想、变量说明、适用场景及原帖链接，方便您理解、应用和进一步探索。
使用时请思考如何将下列模板与有的Alpha表达式结合，创造出新的模板来捕捉和发现市场规律，找到”好“公司和”坏“公司
**使用前请注意：**
*   **过拟合风险**：部分模板可能存在过拟合风险，请谨慎使用，并结合IS-Ladder测试、多市场回测等方法进行验证。
*   **参数调整**：模板中的参数（如时间窗口、数据集字段）需要根据您的具体研究目标和数据特性进行调整。
*   **持续学习**：最好的模板是您自己创造的。希望本文档能激发您的灵感，而不是限制您的思维。

---

## From: Alpha Examples from Learn101

### Momentum after news
**Hypothesis**: After news is released, if a stock takes a longer time to rise, it may show strong evidence of upward momentum, and it could be beneficial to take a long position in it.
**Expression**: `ts_backfill(vec_avg(nws12_prez_4l),504)`
**Settings**: Region: USA, Universe: TOP500, Delay: 1, Decay: 0, Neutralization: INDUSTRY, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **时序相对性 (Step 4)**: 这是一个典型的时序信号。`ts_backfill` 的使用暗示了新闻数据是稀疏的（Step 4.2.4），需要填补空白以维持信号连续性。
*   **运算符深意**: `vec_avg` 用于聚合多维新闻向量，提取核心情绪/强度；`ts_backfill` 确保在无新闻日也能维持上一次的观点，直到新消息到来。
**优化方向**:
*   **去噪 (Step 0)**: 新闻情绪可能存在极端噪音，建议在 `vec_avg` 后增加 `winsorize` 或 `rank`。
*   **从属信号 (Subordinate)**: 叠加 `Social Media Effect`。若新闻情绪好但社媒热度低（噪音少），则放大权重；若社媒过热，可能反转。
*   **门限交易 (Step 5)**: 仅在新闻情绪显著偏离均值时交易，如 `trade_when(abs(zscore(news)) > 1.5, ...)`。

### Pretax Income
**Hypothesis**: Pretax income is a good measure of a company's financial health and profitability.
**Expression**: `quantile(ts_rank(pretax_income,250))`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 4, Neutralization: MARKET, Truncation: 0.01, Pasteurization: ON
**逻辑链深度解析**:
*   **时序相对性 (Step 4)**: `ts_rank(..., 250)` 比较当前收入与过去一年的水平，寻找“自身改善”而非“绝对高收入”。
*   **分布重塑 (Step 0)**: `quantile` 强制将信号拉伸为均匀分布，避免了极值影响，只关注相对排序。
**优化方向**:
*   **区间优化 (Step 2)**: 收入微弱变化可能只是噪音。可改用 `ts_zscore` 并只在 >1 或 <-1 时交易。
*   **从属信号**: 引入 `market_cap`。大市值的收入创新高可能比小市值更稳健（质量溢价）。

### Operating Earnings Yield
**Hypothesis**: If the operating income of a company is currently higher than its past 1 year history, buy the company's stock and vice-versa.
**Expression**: `ts_rank(operating_income,252)`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: SUBINDUSTRY, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **时序相对性 (Step 4)**: 纯粹的时序动量逻辑。`ts_rank` 将当前值映射到历史分位，捕捉“业绩改善”趋势。
**优化方向**:
*   **组内比较 (Step 3)**: 考虑行业周期性。先做 `group_zscore(operating_income, industry)` 再做 `ts_rank`，剔除行业景气度影响，只看个股相对行业的改善。
*   **门限 (Step 5)**: `trade_when(ts_rank > 0.8, ...)` 只做多业绩显著改善的股票。

### Appreciation of liabilities
**Hypothesis**: An increase in the fair value of liabilities could indicate a higher cost than expected.
**Expression**: `-ts_rank(fn_liab_fair_val_l1_a,252)`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: SUBINDUSTRY, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **反向信号**: 负号 `-` 表示这是一个反向指标（负债增加是坏事）。
*   **时序相对性**: 同样基于 `ts_rank`，关注负债相对于自身历史的增长速度。
**优化方向**:
*   **去噪**: 负债数据可能存在跳变，建议先 `winsorize`。
*   **从属信号**: 结合 `cash_flow`。若负债增加但现金流同时也大幅增加（良性杠杆），则不应做空。

### Deferred Revenue
**Hypothesis**: Firms with high deferred revenue will surprise the market in the future when the deferred revenue is recognized.
**Expression**: `ts_backfill(fnd6_drc, 252)/assets`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: SECTOR, Truncation: 1, Pasteurization: ON
**逻辑链深度解析**:
*   **截面比较 (Step 3)**: 除以 `assets` 是为了标准化（Size Adjustment），使其在截面上可比。
*   **数据填补 (Step 0)**: `ts_backfill` 处理财报数据的低频更新特性。
**优化方向**:
*   **行业中性 (Step 3)**: 递延收入在软件/服务业常见，在制造业少见。必须做 `group_zscore(..., sector)` 或 `neutralize`，否则只是在做多特定行业。
*   **时序变化 (Step 4)**: 关注递延收入的 *增长率* `ts_delta`，而不仅仅是绝对值。

### Reducing debt
**Hypothesis**: Take a long position in companies whose debt has decreased compared to the past.
**Expression**: `-ts_quantile(debt, 126)`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: MARKET, Truncation: 0.01, Pasteurization: ON
**逻辑链深度解析**:
*   **时序相对性**: `ts_quantile` 与 `ts_rank` 类似，捕捉债务下降趋势。
**优化方向**:
*   **从属信号**: 结合 `interest_coverage` (利息保障倍数)。只有在偿债能力弱的公司中，债务减少才最重要（困境反转逻辑）。

### Power of leverage
**Hypothesis**: Companies with high liability-to-asset ratios often leverage debt as a strategic tool.
**Expression**: `liabilities/assets`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: MARKET, Truncation: 0.01, Pasteurization: ON
**逻辑链深度解析**:
*   **截面比较 (Step 3)**: 这是一个经典的截面因子（杠杆率）。
**优化方向**:
*   **非线性 (Step 1)**: 杠杆通常是倒U型关系（适度杠杆好，过高杠杆坏）。考虑使用 `bucket` 分段，或 `trade_when` 剔除极端高杠杆。
*   **行业中性**: 银行/地产杠杆天生高，必须行业中性化。

## From: Alpha Examples from Learn102

### Social Media Effect
**Hypothesis**: Poorly performing stocks are discussed more in general on social media platforms.
**Expression**: `-scl12_buzz`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: INDUSTRY, Truncation: 0.01, Pasteurization: ON
**逻辑链深度解析**:
*   **反向指标**: 负号暗示“关注度高=坏事”（可能是负面新闻缠身）。
*   **原始信号**: 直接使用 `buzz`，假设线性关系。
**优化方向**:
*   **去噪 (Step 0)**: 社媒数据极值多，必须 `log` 或 `winsorize`。
*   **从属信号**: 结合 `sentiment`。若关注度高且情感为正，可能是好事；关注度高且情感负，才是做空机会。
*   **门限**: `trade_when(rank(buzz) > 0.9, ...)` 只在极度热门时做空。

### Valuation Disconnect Swing Short
**Hypothesis**: A stock with high momentum and value score correlation suggests a disconnect between the stock's price and its intrinsic value.
**Expression**: `-ts_corr(ts_backfill(fscore_momentum,66),ts_backfill(fscore_value,66),756)`
**Settings**: Region: USA, Universe: TOP200, Delay: 1, Decay: 0, Neutralization: INDUSTRY, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **高阶统计量**: 使用 `ts_corr` 捕捉两个因子之间的动态关系，而非因子本身。
*   **逻辑**: 动量与价值相关性高，意味着价格脱离基本面（泡沫），因此做空（负号）。
**优化方向**:
*   **窗口调整**: 756天（3年）非常长，捕捉的是长期结构变化。可尝试短窗口（如126天）捕捉短期背离。

### Network Dependence
**Hypothesis**: Long stocks of companies whose hub score of customers are low over the past two years.
**Expression**: `-ts_mean(pv13_ustomergraphrank_hub_rank,504)`
**Settings**: Region: USA, Universe: TOP1000, Delay: 1, Decay: 0, Neutralization: INDUSTRY, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **供应链逻辑**: 客户集中度/中心度过高可能意味着风险（依赖大客户）。
*   **平滑 (Step 4)**: `ts_mean(..., 504)` 说明这是一个非常慢的变量，关注长期结构。
**优化方向**:
*   **从属信号**: 结合 `volatility`。高依赖度+高波动 = 极度危险。

## From: Alpha Examples from Learn103

### News-driven Volatility
**Hypothesis**: Stocks of companies that face high differences in their prices after any news release can be subject to varying sentiments.
**Expression**: `(ts_arg_max(ts_backfill(news_session_range, 20), 60))`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 0, Neutralization: SECTOR, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **事件驱动 (Step 4.2.3)**: `ts_arg_max` 寻找过去60天内波动最大的那一天（新闻日）。
*   **运算符深意**: 这不是直接用波动率，而是用“最大波动发生的时间距离”作为信号。
**优化方向**:
*   **衰减逻辑**: 结合 `days_from_last_change` 或 `exp_decay`，让信号随时间减弱。
*   **从属信号**: 叠加 `IV Skew`。若波动大且 Skew 偏空，做空；若 Skew 偏多，做多。

### Implied Volatility Spread as a predictor
**Hypothesis**: If the Call Open interest is higher than the Put Open interest, the stock may rise based on the intensity of the implied volatility spread.
**Expression**: `trade_when(pcr_oi_270 < 1, (implied_volatility_call_270-implied_volatility_put_270), -1)`
**Settings**: Region: USA, Universe: TOP3000, Delay: 1, Decay: 4, Neutralization: MARKET, Truncation: 0.08, Pasteurization: ON
**逻辑链深度解析**:
*   **门限交易 (Step 5)**: `trade_when(pcr_oi < 1, ...)` 是典型的门禁逻辑。只有在看涨持仓量大于看跌时（情绪偏多），才使用 IV Spread 信号。
*   **条件分支**: 不满足条件时给 `-1`（做空），这是一个激进的二元策略。
**优化方向**:
*   **平滑**: IV 数据跳动大，建议对 Spread 做 `ts_mean` 或 `ts_decay_linear`。

## 《151 Trading Strategies》论文精华模板

本部分总结自Zura Kakushadze与Juan Andrés Serur合著的《151 Trading Strategies》一文，重点提炼其中适用于BRAIN平台的股票类策略，并将其泛化为可复用的Alpha模板。

---

### 1. 风险调整后动量模板 (Risk-Adjusted Momentum)

*   **模板表达式**: `ts_mean(ts_delay(returns, <skip_period>), <lookback_period>) / ts_std_dev(ts_delay(returns, <skip_period>), <lookback_period>)`
*   **核心思想**: 这是对经典动量因子的改进。它计算的是过去一段时间（lookback_period）的"时序夏普比率"，即收益均值除以收益波动。同时，`ts_delay`跳过了最近一段时间（skip_period，通常为21天/1个月）的数据，以规避短期反转效应的干扰。该因子旨在寻找那些"高质量"的、持续且平稳的动量。
*   **变量说明**:
    *   `<skip_period>`: 跳过的近期交易日数，如 `21`。
    *   `<lookback_period>`: 计算动量的回看窗口，如 `252`。
*   **适用场景**: 通用性强，适用于构建稳健的动量类Alpha。
*   **逻辑链深度解析**:
    *   **时序标准化 (Step 4)**: 分子是收益均值，分母是波动率。本质是 Rolling Sharpe Ratio。
    *   **去噪 (Step 0)**: `ts_delay` 跳过最近一个月，剔除了短期反转（Short-term Reversal）噪音，只保留中长期动量。
*   **优化方向**:
    *   **从属信号**: 叠加 `turnover`。在低换手率时，动量更可靠（量价配合）。
    *   **残差化**: 先对 returns 做 `regression_neut` 剔除大盘影响，计算纯特异性动量。
*   **适配自**: Section 3.1, "Price-momentum", `Rrisk.adj`

### 2. 标准化盈利超预期模板 (SUE - Standardized Unexpected Earnings)

*   **模板表达式**: `(fnd_eps_q - ts_delay(fnd_eps_q, 4)) / ts_std_dev(fnd_eps_q - ts_delay(fnd_eps_q, 4), 8)`
*   **核心思想**: 捕捉超预期的盈利增长。它计算的是最新一季的EPS相较于去年同期的增量，并用该增量自身过去8个季度的波动性进行标准化。标准化后的值（SUE）越高，代表盈利惊喜越大，是经典的盈利动量因子。
*   **变量说明**:
    *   `fnd_eps_q`: 季度每股收益（EPS）字段。
*   **适用场景**: `Fundamental`（基本面）数据集，用于事件驱动型Alpha。
*   **逻辑链深度解析**:
    *   **季节性调整**: `ts_delay(..., 4)` 比较同比季度，消除季节性影响。
    *   **波动率标准化 (Step 0)**: 除以过去8季度的波动，将“惊喜”转化为标准差单位（Z-Score），使其在不同波动率的公司间可比。
*   **优化方向**:
    *   **事件衰减 (Step 4)**: 叠加 `days_from_last_change`，让 SUE 信号随财报发布时间衰减。
    *   **从属信号**: 叠加 `Analyst Revision`。若 SUE 高且分析师上调预期，信号更强。
*   **适配自**: Section 3.2, "Earnings-momentum", SUE


### 4. 隐含波动率偏斜动量模板 (Implied Volatility Skew Momentum)

*   **模板表达式**: `ts_delta(implied_volatility_call_<window>, <period>) - ts_delta(implied_volatility_put_<window>, <period>)`
*   **核心思想**: 捕捉市场情绪的变化。看涨期权IV的上升通常与乐观情绪相关，而看跌期权IV的上升则与悲观或避险情绪相关。该模板计算Call IV的变化量与Put IV变化量之差，旨在做多情绪改善、做空情绪恶化的股票。
*   **变量说明**:
    *   `implied_volatility_call_<window>`: 不同期限的看涨期权隐含波动率。
    *   `implied_volatility_put_<window>`: 不同期限的看跌期权隐含波动率。
    *   `<period>`: 计算IV变化的时间窗口，如 `21` (月度变化)。
*   **适用场景**: `Option`（期权）数据集，用于捕捉短中期市场情绪变化。
*   **逻辑链深度解析**:
    *   **时序变化 (Step 4)**: 关注的是 IV 的 *变化* (`ts_delta`) 而非绝对值。
    *   **情绪差**: Call IV 涨幅 > Put IV 涨幅 -> 情绪改善。
*   **优化方向**:
    *   **门限**: `trade_when(abs(skew_delta) > threshold, ...)` 只在情绪剧烈变化时交易。
    *   **事件驱动**: 在财报前（IV 高企时）该策略可能失效，需用 `days_to_earnings` 过滤。
*   **适配自**: Section 3.5, "Implied volatility"

### 5. 残差动量模板 (Residual Momentum)

*   **模板表达式**: `ts_mean(regression_neut(regression_neut(regression_neut(returns, <factor_1/>), <factor_2/>), <factor_3/>), <window/>)`
*   **核心思想**: 提纯动量信号。传统动量可能包含了市场Beta、市值、价值等多种因子的敞口。此模板通过连续的中性化（例如依次对`<factor_1/>`, `<factor_2/>`, `<factor_3/>`执行`regression_neut`）剥离可被通用因子解释的部分，然后仅对无法被解释的"残差等价物"部分计算动量。
*   **变量说明**:
    *   `<factor_1/>`, `<factor_2/>`, `<factor_3/>`: 市场通用因子，如 `mkt_beta`, `size_factor`, `value_factor`。
    *   `<window/>`: 计算残差动量的时间窗口。
*   **适用场景**: 通用性强，是因子提纯、构建高质量Alpha的关键步骤。
*   **逻辑链深度解析**:
    *   **提纯 (Step 0)**: 通过连续 `regression_neut` 剥离 Beta、Size、Value 等风格暴露。
    *   **时序动量**: 对剥离后的残差求 `ts_mean`。
*   **优化方向**:
    *   **加权**: 使用 `ts_decay_linear` 代替 `ts_mean`，给予近期残差更大权重。
    *   **组内比较**: 在残差基础上再做 `group_rank`，寻找行业内最强特异动量。
*   **适配自**: Section 3.7, "Residual momentum"

### 6. 风险加权回归均值回归模板 (Weighted Regression Mean-Reversion)

*   **模板表达式**: `reverse(regression_neut(multiply(returns, power(inverse(ts_std_dev(returns, <window/>)), 2)), <group_matrix/>))`
*   **核心思想**: 这是对标准行业中性化均值回归的增强。在对收益率进行行业中性化时，它为不同股票赋予了不同的权重。具体来说，它给历史波动率较低的股票更高的权重，认为这些股票的收益率数据更"可靠"，在计算行业均值时应占更大比重。
*   **变量说明**:
    *   `<group_matrix>`: 行业或分组的哑变量矩阵。
    *   `weights`: 回归权重，通常是可靠性的度量，如 `1/variance`。
    *   `<window>`: 计算波动率的时间窗口。
*   **适用场景**: 适用于任何需要进行组内中性化或回归剥离的场景，尤其是当组内成员的信号质量或波动性差异较大时。
*   **逻辑链深度解析**:
    *   **加权最小二乘 (WLS)**: 使用 `1/variance` 作为权重，认为低波动的股票信息更可靠。
    *   **均值回归**: `reverse` 捕捉残差的反转。
*   **优化方向**:
    *   **从属信号**: 引入 `liquidity` 权重。流动性好的股票回归更快。
*   **适配自**: Section 3.10, "Mean-reversion – weighted regression"

### 7. 移动平均线交叉模板 (Moving Average Crossover)

*   **模板表达式**: `sign(ts_mean(<price/>, <short_window>) - ts_mean(<price/>, <long_window>))`
*   **核心思想**: 经典的趋势跟踪策略。当短期均线上穿长期均线（"金叉"）时，表明短期趋势走强，产生买入信号。当短期均线下穿长期均线（"死叉"）时，表明趋势走弱，产生卖出信号。
*   **变量说明**:
    *   `<price/>`: `close`, `vwap` 等价格字段。
    *   `<short_window>`: 短期均线窗口，如 `10`, `20`。
    *   `<long_window>`: 长期均线窗口，如 `50`, `100`。
*   **适用场景**: 适用于趋势性较强的市场或资产。
*   **逻辑链深度解析**:
    *   **低通滤波**: MA 本质是滤除高频噪音。
    *   **二元信号**: `sign` 输出 +1/-1，不包含强度信息。
*   **优化方向**:
    *   **连续化 (Step 1)**: 去掉 `sign`，直接使用差值并标准化 (`zscore`)，保留强度信息。
    *   **从属信号**: 结合 `ADX` (趋势强度指标)。只有在趋势强时才使用 MA 交叉。
*   **适配自**: Section 3.12, "Two moving averages"



### 9. 渠道突破模板 (Channel Breakout)

*   **模板表达式**: `alpha = if_else(greater(close, ts_max(high, <window/>)), 1, if_else(less(close, ts_min(low, <window/>)), -1, 0)); reverse(alpha)`
*   **核心思想**: 这是一个经典的反转策略。它定义了一个由过去N日最高价和最低价构成的价格渠道（Channel）。当价格向上突破渠道上轨时，认为市场过热，产生卖出信号（-1）；当价格向下突破渠道下轨时，认为市场超卖，产生买入信号（+1）。
*   **变量说明**:
    *   `<window>`: 定义渠道的时间窗口，如 `20`。
*   **适用场景**: 适用于有均值回归特性的市场或个股。
*   **逻辑链深度解析**:
    *   **区间突破 (Step 2)**: 典型的“只在尾部交易”逻辑。中间区间为 0。
    *   **反转逻辑**: `reverse` 赌突破是假突破（False Breakout）。
*   **优化方向**:
    *   **顺势/逆势切换**: 结合 `volatility`。低波时做反转（假突破），高波时做顺势（真突破）。
*   **适配自**: Section 3.15, "Channel"


### 11. 价值因子基础模板 (Value Factor)

*   **模板表达式**: `group_rank(<book_value/> / <market_cap/>)`
*   **核心思想**: 经典的价值投资策略。它旨在买入账面价值相对于市场价值被低估的"价值股"，并卖出被高估的"成长股"。最核心的衡量指标是账面市值比（Book-to-Price / Book-to-Market Ratio）。
*   **变量说明**:
    *   `<book_value/>`: 公司账面价值或每股净资产字段。
    *   `<market_cap/>`: 公司市值或收盘价字段。
*   **适用场景**: `Fundamental` (基本面) 数据集，作为构建多因子模型的基础因子之一。
*   **逻辑链深度解析**:
    *   **组内比较 (Step 3)**: 价值因子在不同行业间不可比（如科技 vs 银行），必须用 `group_rank`。
*   **优化方向**:
    *   **去噪**: 先 `winsorize` 再 `group_rank`。
    *   **从属信号**: 叠加 `Quality` (ROE)。避免买入“价值陷阱”（便宜但烂的公司）。
*   **适配自**: Section 3.3, "Value"



### 13. 配对交易均值回归框架 (Pairs Trading)

*   **模板表达式**: `signal_A = (close_A - close_B) - ts_mean(close_A - close_B, <window>); reverse(signal_A)`
*   **核心思想**: 寻找历史上高度相关的两只股票（一个"配对"），当它们的价差（spread）偏离历史均值时进行套利。如果价差过大，则做空价高的股票、做多价低的股票，赌价差会回归。这是一个经典的统计套利和均值回归策略。
*   **变量说明**:
    *   `close_A`, `close_B`: 配对股票A和B的价格序列。
    *   `<window>`: 计算历史价差均值的时间窗口。
*   **适用场景**: 适用于同一行业内业务高度相似的公司，是构建市场中性策略的基础。
*   **逻辑链深度解析**:
    *   **协整关系**: 构造平稳序列 `Spread`。
    *   **均值回归**: 赌 Spread 回归均值。
*   **优化方向**:
    *   **动态阈值**: 使用 `ts_std_dev(Spread)` 设定动态开仓线（如 2倍标准差）。
    *   **止损**: 增加 `trade_when(abs(Spread) > 4*std, 0, ...)` 防止协整破裂。
*   **适配自**: Section 3.8, "Pairs trading"

---

## 补充模板

### A. Analyst交叉分组打底（模板名：示例）
*   **核心结构**: `financial_data = ts_backfill(<vec_func/>(<analyst_metric/>), 60); gp = group_cartesian_product(country, industry); <ts_operator/>(<group_operator/>(financial_data, gp), <window/>)`
*   **思想**: 先对分析师字段做向量聚合（`vec_avg`、`vec_kurtosis`、`vec_ir`等），用`group_cartesian_product`构建国家×行业组合，再做组内标准化/中性化+时序处理，形成稳定的截面信号。
*   **变量要点**: `analyst_metric`覆盖`mdl26_*`、`star_arm_*`等Analyst/SmartEstimate场景；`vec_func`选择聚合方式；`group_operator`用于行业/国家组内的scale或neutralize；`ts_operator`用于时间平滑（`ts_mean`、`ts_zscore`等）；`window`在20/60/90/200之间取值。
*   **适用场景**: 适合Analyst情感、预期修正类主题，想要跨国+行业分组的稳健截面信号。
*   **逻辑链深度解析**:
    *   **数据填补 (Step 0)**: 分析师数据稀疏，必须 `ts_backfill`。
    *   **精细分组 (Step 3)**: `group_cartesian_product` 实现了“国家x行业”的精细化中性化，适合全球策略。
*   **优化方向**:
    *   **运算符选择**: `vec_ir` (信息比率) 比 `vec_avg` 更能体现分析师的一致性。

### B. 双重中性化（模板名：双重中性化:以Analyst15为例）
*   **核心结构**: 与上类似，先`ts_backfill(vec_func(Analyst15字段), 60)`，再按国家×行业分组，做组内中性化与时序处理。
*   **思想**: 针对`anl15_*`增长/估值/分红等字段，在截面层面做两次中性化（向量聚合后+组内处理），用于剥离共性行业/国家暴露。
*   **变量要点**: 数据集中`anl15_*`覆盖多期增长率、PE、估值、分红等；`vec_func`与`ts_operator`选择决定信号平滑度；窗口建议60–200以保证填补稳定。
*   **适用场景**: Analyst15预期修正、估值再定价类信号，需要同时消化国家+行业噪音的场景。
*   **逻辑链深度解析**:
    *   **多重剥离**: 彻底消除风格暴露，追求纯 Alpha。
*   **优化方向**:
    *   **顺序**: 先做行业中性，再做国家中性，通常更符合基本面逻辑。

### C. 组间比较（模板名：组间比较_GLB_topdiv）
*   **核心结构**: 先在`country × <group1/>`分组内对回填后的向量聚合结果做`ts_zscore`和`group_zscore`，再计算组均值/极值（`group_min/median/max/sum/count`），用`resid = <compare/>(alpha, alpha_gpm)`求组间残差，最后再做组内+时序处理。
*   **思想**: 对同一层级（如行业/子行业/交易所）之间的相对强弱做剥离，得到“相对组均值”的残差信号，适合跨组对比的Alpha挖掘。
*   **变量要点**: `analyst_field`来源于`fnd8_*`基本面/现金流字段；`vec_op`可选`vec_max/avg/min`；`compare`可用`regression_neut`或`signed_power`提取残差；`t_window`取20/60/200/600，控制平滑与稳定性。
*   **适用场景**: GLB区域的分红/现金流因子（topdiv）在国家+行业框架下的相对价值比较，关注跨组差异的策略。
*   **逻辑链深度解析**:
    *   **相对价值**: 关注的是“我在我的组里是否优秀”，而不是“我绝对值多少”。
*   **优化方向**:
    *   **非线性**: 使用 `rank` 代替原始值计算残差，对异常值更鲁棒。

### D. 组间比较（Analyst15版，模板名：组间比较_glb_topdiv_anl15）
*   **核心结构**: 与上一模板相同，但`analyst_field`替换为`anl15_*`系列的增长/估值/分红字段。
*   **思想**: 通过对Analyst15增长与估值预期的组间残差建模，捕捉行业/国家层面的相对高低估与预期修正。
*   **变量要点**: `group1`可选industry/subindustry/sector/exchange；`compare`与`group_stats`同上；`ts_op`和`group_op`用于残差后再标准化和时序平滑。
*   **适用场景**: 全球范围GLB，基于Analyst15预期数据的组间相对价值或动量信号。
*   **逻辑链深度解析**:
    *   **预期差**: 寻找行业内被分析师低估/高估的股票。
*   **优化方向**:
    *   **时序叠加**: 结合 `ts_delta`，寻找“行业内预期提升最快”的股票。

### E. 顾问分析示例（模板名：顾问分析示例）
*   **核心结构**: `financial_data = ts_backfill(<mixdata/>, 90); gp = industry; <ts_operator/>(<group_operator/>(financial_data, gp), <window/>)`
*   **思想**: 直接对`anl69_*`多字段做90日回填，行业组内标准化后再做时序平滑，生成简洁的行业中性信号。
*   **变量要点**: `mixdata`覆盖`anl69_*`的EPS/EBIT/现金分红/目标价/报告日期等；`ts_operator`可用`ts_zscore`、`ts_scale`、`ts_rank`等；`window`提供60/120/220/600可调节频率。
*   **适用场景**: Analyst69数据驱动的行业内预期跟踪、财报节奏/指引变化监控。
*   **逻辑链深度解析**:
    *   **标准流程**: 填补 -> 截面标准化 -> 时序平滑。这是构建稳健因子的标准三板斧。
*   **优化方向**:
    *   **事件驱动**: 在财报日前后缩短 `ts_mean` 的窗口，提高灵敏度。

---

## 新增模板（CAPM與估值、分析師期限、期權、搜尋優化）

### 1. CAPM殘差模板（市場/行業中性收益）
*   **表達式**: `ts_regression(returns, group_mean(returns, log(ts_mean(cap,21)), sector), 252, rettype=0)`。
*   **核心思想**: 回歸剔除市場/行業暴露，保留超額收益殘差作為Alpha。
*   **適用場景**: 通用起手式，回歸殘差可作後續動量或價值信號的底板。
*   **優化**: 改`rettype=2`獲取beta斜率，用於風險排序或低/高beta組合；可加入`winsorize`、`ts_backfill`預處理。

### 2. CAPM廣義殘差（任意特徵）
*   **表達式**: `data = winsorize(ts_backfill(<data>,63), std=4); gpm = group_mean(data, log(ts_mean(cap,21)), sector); resid = ts_regression(data, gpm, 252, rettype=0)`。
*   **核心思想**: 將任意特徵去除組均值成分，提取行業相對的特異性部分。
*   **適用場景**: 基本面、情緒、替代數據的組內殘差提純。
*   **優化**: 先`group_zscore`再回歸；對`resid`再做`ts_zscore`或`ts_mean`平滑。

### 3. CAPM Beta排序模板
*   **表達式**: `target_data = winsorize(ts_backfill(<target>,63), std=4); market_data = winsorize(ts_backfill(<market>,63), std=4); beta = ts_regression(target_data, group_mean(market_data, log(ts_mean(cap,21)), sector), 252, rettype=2)`。
*   **核心思想**: 提取行業內相對beta，作為風險/防禦排序；低beta偏防禦，高beta偏進攻。
*   **優化**: 行業或國家分組；可按beta分桶做長低/短高，或反向用於高波段套利。

### 4. 實際-預估差異模板（Analyst Surprise）
*   **表達式**: `group_zscore(subtract(group_zscore(<act>, industry), group_zscore(<est>, industry)), industry)`。
*   **核心思想**: 行業內標準化後的實際值與預估值差，捕捉超預期或低於預期的驚喜。
*   **適用場景**: analyst7/analyst14/earnings估值類字段。
*   **優化**: 對差分再做`ts_zscore`；門檻交易只在|z|>1.5時開倉。

### 5. 分析師期限結構模板（近遠期預估斜率）
*   **表達式**: `group_zscore(subtract(group_zscore(anl14_mean_eps_<p1>, industry), group_zscore(anl14_mean_eps_<p2>, industry)), industry)`，`<p1>/<p2>`為fp1/fp2/fy1/fy2等。
*   **核心思想**: 比較短期與長期預估的行業內斜率，捕捉預期加速或鈍化。
*   **適用場景**: analyst14/15 期別字段；適用成長/拐點挖掘。
*   **優化**: 擴展到多期間差分或`ts_delta`跟蹤斜率變化；對斜率做`rank`或`winsorize`。

### 6. 期權Greeks淨值模板
*   **表達式**: `group_operator(<put_greek> - <call_greek>, <group>)`，Greek可選Delta/Gamma/Vega/Theta。
*   **核心思想**: 同組內看多vs看空的期權敏感度差，反映隱含情緒或凸性差異。
*   **適用場景**: Option數據集；行業或市值分組下的情緒/波動信號。
*   **優化**: 多Greek加權組合；對淨值再`ts_mean`平滑；事件期(財報)可降權或過濾。

### 7. IV Skew動量擴展
*   **表達式**: `ts_delta(implied_volatility_call_<w>, <p>) - ts_delta(implied_volatility_put_<w>, <p>)`。
*   **核心思想**: Call與Put隱含波動變化差捕捉情緒轉折；可做多情緒改善、做空情緒惡化。
*   **優化**: 加`trade_when(abs(skew)>thr)`門檻；財報前後縮窗；行業中性。

### 8. 殘差動量精簡版
*   **表達式**: `res = regression_neut(returns, <common_factor_matrix>); ts_mean(res, <window>)`。
*   **核心思想**: 先剝離市場/風格暴露，再對特異收益做動量；較原版多重回歸更輕量。
*   **優化**: 使用`ts_decay_linear`增加近期權重；行業內`group_rank`提升截面穩定度。

### 9. 分紅/現金流組間殘差（簡版）
*   **表達式**: `alpha = ts_zscore(ts_backfill(<cf_or_div_field>,90)); g = group_mean(alpha, <group>, <weight_opt>); resid = alpha - g; group_zscore(resid, <group>)`。
*   **核心思想**: 先回填平滑，再对組均值做殘差，捕捉組內相對高/低分紅或現金流質量。
*   **適用場景**: fnd8/fnd6/topdiv等分紅現金流字段；行業/國家分組。
*   **優化**: 權重可用log(cap)或vol逆；對resid再做`ts_mean`平滑。

---

## 模板格式说明

每个模板使用以下占位符格式：
- `<ts_op/>` - 时间序列操作符，如 `ts_rank`, `ts_mean`, `ts_delta`, `ts_ir`, `ts_stddev`, `ts_zscore`
- `<group_op/>` - 分组操作符，如 `group_rank`, `group_neutralize`, `group_zscore`
- `<vec_op/>` - 向量操作符，如 `vec_avg`, `vec_sum`, `vec_max`, `vec_min`, `vec_stddev`
- `<field/>` - 数据字段占位符
- `<d/>` - 时间窗口参数，常用值: `{5, 22, 66, 126, 252, 504}`
- `<group/>` - 分组字段，如 `industry`, `sector`, `subindustry`, `market`

---

## 第一部分：基础结构模板 (TPL-001 ~ TPL-010)

### TPL-001: 基本面时序排名
```
模板: <group_op/>(<ts_op/>(<field/>, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore`, `ts_delta`, `ts_ir` | 时序比较操作 |
| `<group_op/>` | `group_rank`, `group_zscore`, `group_neutralize` | 截面比较操作 |
| `<field/>` | 基本面字段: `eps`, `sales`, `assets`, `roe`, `roa` | 公司财务数据 |
| `<d/>` | `66`, `126`, `252` | 季度/半年/年 |
| `<group/>` | `industry`, `sector` | 行业分组 |

**示例**:
```
group_rank(ts_rank(eps, 252), industry)
group_zscore(ts_ir(sales, 126), sector)
```

---

### TPL-002: 利润/规模比率模板
```
模板: <ts_op/>(<profit_field/>/<size_field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore`, `ts_mean`, `ts_delta` | 时序操作 |
| `<profit_field/>` | `net_income`, `ebitda`, `operating_income`, `gross_profit` | 利润类字段 |
| `<size_field/>` | `assets`, `cap`, `sales`, `equity` | 规模类字段 |
| `<d/>` | `66`, `126`, `252` | 中长期窗口 |

**示例**:
```
ts_rank(net_income/assets, 252)
ts_zscore(ebitda/cap, 126)
ts_rank(operating_income/cap, 252)^2
```

---

### TPL-003: 向量数据处理模板 (VECTOR字段必用)
```
模板: <ts_op/>(<vec_op/>(<vector_field/>), <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_mean`, `ts_delta`, `ts_ir`, `ts_zscore` | 时序操作 |
| `<vec_op/>` | `vec_avg`, `vec_sum`, `vec_max`, `vec_min`, `vec_stddev` | 向量聚合 |
| `<vector_field/>` | 分析师数据: `anl4_*`, `analyst_*`, `oth41_*` | VECTOR类型字段 |
| `<d/>` | `22`, `66`, `126` | 短中期窗口 |

**示例**:
```
ts_delta(vec_avg(anl4_eps_mean), 22)
ts_rank(vec_sum(analyst_estimate), 66)
ts_ir(vec_avg(oth41_s_west_eps_ftm_chg_3m), 126)
```

---

### TPL-004: 双重中性化模板
```
模板:
a = <ts_op/>(<field/>, <d/>);
a1 = group_neutralize(a, bucket(rank(cap), range="<range/>"));
group_neutralize(a1, <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_zscore`, `ts_rank`, `ts_ir` | 时序操作 |
| `<field/>` | 任意数据字段 | 主信号 |
| `<d/>` | `66`, `126`, `252` | 时间窗口 |
| `<range/>` | `"0.1,1,0.1"`, `"0,1,0.1"` | 市值分组范围 |
| `<group/>` | `industry`, `sector`, `subindustry` | 行业分组 |

**示例**:
```
a = ts_zscore(fnd72_s_pit_or_is_q_spe_si, 252);
a1 = group_neutralize(a, bucket(rank(cap), range="0.1,1,0.1"));
group_neutralize(a1, subindustry)
```

---

### TPL-005: 回归中性化模板
```
模板:
a = <ts_op/>(<field/>, <d/>);
a1 = group_neutralize(a, bucket(rank(cap), range="<range/>"));
a2 = group_neutralize(a1, <group/>);
b = ts_zscore(cap, <d/>);
b1 = group_neutralize(b, <group/>);
regression_neut(a2, b1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_zscore`, `ts_rank` | 时序操作 |
| `<field/>` | 基本面或其他字段 | 主信号 |
| `<d/>` | `252`, `504` | 长期窗口 |
| `<range/>` | `"0.1,1,0.1"` | 市值分组 |
| `<group/>` | `subindustry`, `sector` | 行业分组 |

---

### TPL-006: 基本面动量模板
```
模板: log(ts_mean(<field/>, <d_short/>)) - log(ts_mean(<field/>, <d_long/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | `anl4_{data}_{stats}`, 基本面字段 | 数据字段 |
| `<d_short/>` | `20`, `44` | 短期窗口 |
| `<d_long/>` | `44`, `126` | 长期窗口 |

**示例**:
```
log(ts_mean(anl4_eps_mean, 44)) - log(ts_mean(anl4_eps_mean, 20))
```

---

### TPL-007: 财报事件驱动模板
```
模板:
event = ts_delta(<fundamental_field/>, -1);
if_else(event != 0, <alpha/>, nan)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<fundamental_field/>` | `assets`, `sales`, `eps` | 基本面字段 |
| `<alpha/>` | 主信号表达式 | 事件发生时的Alpha |

**扩展版**:
```
change = if_else(days_from_last_change(<field/>) == <days/>, ts_delta(close, <d/>), nan)
```

---

### TPL-008: 标准化回填模板
```
模板: <ts_op/>(winsorize(ts_backfill(<field/>, <d_backfill/>), std=<std/>), <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_decay_linear`, `ts_zscore` | 时序操作 |
| `<field/>` | 低频数据字段 | 需要回填的字段 |
| `<d_backfill/>` | `115`, `120`, `180` | 回填窗口 |
| `<std/>` | `4`, `3`, `5` | winsorize标准差 |
| `<d/>` | `10`, `22`, `60` | 操作窗口 |

**示例**:
```
ts_decay_linear(-densify(zscore(winsorize(ts_backfill(anl4_adjusted_netincome_ft, 115), std=4))), 10)
ts_rank(winsorize(ts_backfill(<data>, 120), std=4), 60)
```

---

### TPL-009: 信号质量分组模板
```
模板:
signal = <ts_op/>(<field/>, <d/>);
credit_quality = bucket(rank(ts_delay(signal, 1), rate=0), range="<range/>");
group_neutralize(<decay_op/>(signal, k=<k/>), credit_quality)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore` | 信号计算 |
| `<field/>` | 任意数据字段 | 主字段 |
| `<d/>` | `60`, `120` | 窗口 |
| `<range/>` | `"0.2,1,0.2"` | 分组范围 |
| `<decay_op/>` | `ts_weighted_decay` | 衰减操作 |
| `<k/>` | `0.5`, `0.3` | 衰减系数 |

---

### TPL-010: 复合分组中性化
```
模板: group_neutralize(<alpha/>, densify(<group1/>)*1000 + densify(<group2/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<group1/>` | `subindustry`, `sector` | 主分组 |
| `<group2/>` | `country`, `exchange` | 次分组 |

---

## 第二部分：量价类模板 (TPL-101 ~ TPL-120)

### TPL-101: 换手率反转
```
模板: -<ts_op/>(volume/sharesout, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_mean`, `ts_rank`, `ts_std_dev` | 时序统计 |
| `<d/>` | `5`, `22`, `66` | 短中期窗口 |

**示例**:
```
-ts_mean(volume/sharesout, 22)
-ts_std_dev(volume/sharesout, 22)
```

---

### TPL-102: 量稳换手率 (STR)
```
模板: -ts_std_dev(volume/sharesout, <d1/>)/ts_mean(volume/sharesout, <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d1/>` | `20`, `22` | 波动计算窗口 |
| `<d2/>` | `20`, `22` | 均值计算窗口 |

**优化版**:
```
模板: -group_neutralize(ts_std_dev(volume/sharesout, <d/>)/ts_mean(volume/sharesout, <d/>), bucket(rank(cap), range="0.1,1,0.1"))
```

---

### TPL-103: 价格反转模板
```
模板: -<ts_op/>(<price_field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_delta`, `ts_mean`, `ts_rank` | 时序操作 |
| `<price_field/>` | `close`, `returns`, `close/open-1`, `open/ts_delay(close,1)-1` | 价格/收益字段 |
| `<d/>` | `3`, `5`, `22` | 短期窗口 |

**示例**:
```
-ts_delta(close, 5)                    # 价格变化反转
-ts_mean(returns, 22)                  # 收益均值反转
-ts_mean(close/open-1, 22)             # 日内收益反转
-(open/ts_delay(close,1)-1)            # 隔夜收益反转
```

---

### TPL-104: 价格乖离率
```
模板: -(close - ts_mean(close, <d/>))/ts_mean(close, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d/>` | `5`, `22`, `66` | MA周期 |

---

### TPL-105: 量价相关性
```
模板: -ts_corr(<price_field/>, <volume_field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<price_field/>` | `close`, `returns`, `abs(returns)` | 价格类 |
| `<volume_field/>` | `volume`, `volume/sharesout`, `adv20` | 成交量类 |
| `<d/>` | `22`, `66`, `126` | 相关性窗口 |

---

### TPL-106: 跳跃因子
```
模板: -group_neutralize(ts_mean((close/open-1) - log(close/open), <d/>), bucket(rank(cap), range="0.1,1,0.1"))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d/>` | `22`, `30`, `66` | 平均窗口 |

**带成交量增强版**:
```
模板: -group_neutralize(ts_mean((close/open-1) - log(close/open), <d/>) * ts_rank(volume, 5), bucket(rank(cap), range="0.1,1,0.1"))
```

---

### TPL-107: 指数衰减动量
```
模板: -ts_decay_exp_window(<field/>, <d/>, factor=<f/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | `returns`, `returns*(volume/sharesout)`, `close/open-1` | 收益类字段 |
| `<d/>` | `22`, `66`, `126` | 衰减窗口 |
| `<f/>` | `0.04`, `0.1`, `0.5`, `0.9` | 衰减因子，越小衰减越快 |

---

### TPL-108: 成交量周期函数 (VOC)
```
模板:
m_minus = ts_mean(volume, <d_long/>) - ts_mean(volume, <d_short/>);
delta = (ts_max(m_minus, <d_short/>) - m_minus)/(ts_max(m_minus, <d_short/>) - ts_min(m_minus, <d_short/>));
<weight1/>*delta + <weight2/>*ts_delay(delta, 1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d_long/>` | `30`, `66` | 长期均值窗口 |
| `<d_short/>` | `10`, `22` | 短期均值窗口 |
| `<weight1/>` | `0.33`, `0.5` | 当日权重 |
| `<weight2/>` | `0.67`, `0.5` | 前日权重 |

---

### TPL-109: 市场相关性因子
```
模板:
mkt_ret = group_mean(returns, 1, market);
pt = ts_corr(returns, mkt_ret, <d/>);
rank(1/(2*(1-pt)))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d/>` | `10`, `22`, `66` | 相关性窗口 |

---

### TPL-110: 成交量趋势模板
```
模板: ts_decay_linear(volume/ts_sum(volume, <d_long/>), <d_short/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d_long/>` | `252`, `504` | 长期总量窗口 |
| `<d_short/>` | `10`, `22` | 衰减窗口 |

---

### TPL-111: VWAP收益相关
```
模板:
returns > -<threshold/> ? (ts_ir(ts_corr(ts_returns(vwap, 1), ts_delay(group_neutralize(<field/>, market), <d1/>), <d2/>), <d2/>)) : -1
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<threshold/>` | `0.1`, `0.05` | 收益阈值 |
| `<field/>` | 任意数据字段 | 信号字段 |
| `<d1/>` | `30`, `60` | 延迟窗口 |
| `<d2/>` | `90`, `120` | 相关性窗口 |

---

### TPL-112: 动量因子创建
```
模板: ts_sum(winsorize(ts_backfill(<data/>, <day/>), std=4.0), <n/>*21) - ts_sum(winsorize(ts_backfill(<data/>, <day/>), std=4.0), <m/>*21)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<data/>` | `returns`, 基本面字段 | 数据字段 |
| `<day/>` | `120`, `180` | 回填窗口 |
| `<n/>` | `6`, `12` | 长期月数 |
| `<m/>` | `1`, `0.1*n` | 短期月数 |

---

### TPL-113: 线性衰减排名
```
模板: -ts_rank(ts_decay_linear(<field/>, <d1/>), <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | `percent`, 任意时序信号 | 输入信号 |
| `<d1/>` | `10`, `22`, `150` | 衰减窗口 |
| `<d2/>` | `50`, `126` | 排名窗口 |

---

## 第三部分：情绪/新闻类模板 (TPL-201 ~ TPL-220)

### TPL-201: 情绪差值模板
```
模板: <ts_op/>(rank(ts_backfill(<positive_sentiment/>, <d/>)) - rank(ts_backfill(<negative_sentiment/>, <d/>)), <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_mean`, `ts_rank`, `ts_zscore` | 时序操作 |
| `<positive_sentiment/>` | 正面情绪字段 | 积极信号 |
| `<negative_sentiment/>` | 负面情绪字段 | 消极信号 |
| `<d/>` | `20`, `30` | 回填窗口 |
| `<d2/>` | `5`, `22` | 比较窗口 |

---

### TPL-202: 新闻情绪回归残差
```
模板:
sentiment = ts_backfill(ts_delay(<vec_op/>(<sentiment_field/>), 1), <d1/>);
vhat = ts_regression(volume, sentiment, <d2/>);
ehat = -ts_regression(returns, vhat, <d3/>);
group_rank(ehat, bucket(rank(cap), range="0,1,0.1"))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<vec_op/>` | `vec_avg`, `vec_sum` | 情绪聚合方式 |
| `<sentiment_field/>` | `scl12_sentiment`, `snt_buzz_ret`, `nws18_relevance` | 情绪数据 |
| `<d1/>` | `20`, `30` | 回填窗口 |
| `<d2/>` | `120`, `250` | 成交量回归窗口 |
| `<d3/>` | `250`, `750` | 收益回归窗口 |

---

### TPL-203: 社交媒体情绪
```
模板: rank(<vec_op/>(scl12_alltype_buzzvec) * <vec_op/>(scl12_sentiment))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<vec_op/>` | `vec_sum`, `vec_avg` | 向量聚合 |

**带条件版**:
```
模板:
sent_vol = vec_sum(scl12_alltype_buzzvec);
trade_when(rank(sent_vol) > 0.95, -zscore(scl12_buzz)*sent_vol, -1)
```

---

### TPL-204: 条件情绪过滤
```
模板:
group_rank(
sigmoid(if_else(ts_zscore(<sentiment_field/>, <d/>) > <threshold/>, ts_zscore(<sentiment_field/>, <d/>), 0)),
<group/>
)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<sentiment_field/>` | 情绪字段 | 情绪数据 |
| `<d/>` | `22`, `30`, `66` | zscore窗口 |
| `<threshold/>` | `1`, `1.5`, `2` | z-score阈值 |
| `<group/>` | `industry`, `sector` | 分组字段 |

---

### TPL-205: 情绪+波动率复合
```
模板: log(1 + sigmoid(ts_zscore(<sentiment_field/>, <d1/>)) * sigmoid(ts_zscore(<volatility_field/>, <d2/>)))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<sentiment_field/>` | 情绪字段 | 情绪数据 |
| `<volatility_field/>` | `option8_*`, 波动率字段 | 波动率数据 |
| `<d1/>` | `30`, `66` | 情绪窗口 |
| `<d2/>` | `30`, `66` | 波动率窗口 |

---

### TPL-206: 指数衰减情绪
```
模板: ts_decay_exp_window(vec_avg(<sentiment_field/>), <d/>, <factor/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<sentiment_field/>` | `mws85_sentiment`, `nws18_ber` | 情绪向量字段 |
| `<d/>` | `10`, `22` | 衰减窗口 |
| `<factor/>` | `0.9`, `0.7` | 衰减因子 |

**双情绪组合**:
```
decayed_sentiment_1 = ts_decay_exp_window(vec_avg(mws85_sentiment), 10, 0.9);
decayed_sentiment_2 = ts_decay_exp_window(vec_avg(nws18_ber), 10, 0.9);
decayed_sentiment_1 + decayed_sentiment_2
```

---

### TPL-207: 新闻结果排名
```
模板:
percent = ts_rank(vec_stddev(<news_field/>), <d1/>);
-ts_rank(ts_decay_linear(percent, <d2/>), <d1/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<news_field/>` | `nws12_prez_result2` | 新闻数据 |
| `<d1/>` | `50`, `66` | 排名窗口 |
| `<d2/>` | `150`, `252` | 衰减窗口 |

---

### TPL-208: 分组行业提取情绪
```
模板: scale(group_extra(ts_sum(sigmoid(ts_backfill(<data/>, <d1/>)), <d2/>) - ts_sum(sigmoid(ts_backfill(<data/>, <d1/>)), <d2/>), 0.5, densify(industry)))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<data/>` | 情绪或基本面字段 | 数据字段 |
| `<d1/>` | `180`, `252` | 回填窗口 |
| `<d2/>` | `3`, `5` | 求和窗口 |

---

## 第四部分：期权类模板 (TPL-301 ~ TPL-320)

### TPL-301: 期权希腊字母差值
```
模板: <group_op/>(<put_greek/> - <call_greek/>, <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<group_op/>` | `group_rank`, `group_neutralize`, `group_zscore` | 分组操作 |
| `<put_greek/>` | `put_delta`, `put_gamma`, `put_theta`, `put_vega` | Put希腊字母 |
| `<call_greek/>` | `call_delta`, `call_gamma`, `call_theta`, `call_vega` | Call希腊字母 |
| `<group/>` | `industry`, `sector` | 分组字段 |

---

### TPL-302: 期权价格信号
```
模板: group_rank(<ts_op/>(<vec_op/>(<option_price_field/>)/close, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_scale`, `ts_rank`, `ts_zscore` | 时序操作 |
| `<vec_op/>` | `vec_max`, `vec_avg` | 向量操作 |
| `<option_price_field/>` | 期权价格字段 | 期权数据 |
| `<d/>` | `66`, `120`, `252` | 时间窗口 |
| `<group/>` | `industry`, `sector` | 分组字段 |

---

### TPL-303: 期权波动率信号
```
模板: sigmoid(<ts_op/>(<opt_high/> - <opt_close/>, <d/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_ir`, `ts_stddev`, `ts_zscore`, `ts_mean` | 波动性操作 |
| `<opt_high/>` | 期权高价字段 | 期权最高价 |
| `<opt_close/>` | 期权收盘价字段 | 期权收盘价 |
| `<d/>` | `120`, `250`, `504` | 长期窗口 |

**说明**: 期权波动类因子通常需要较长窗口(120-504天)来捕捉稳定信号

---

### TPL-304: 隐含波动率比率
```
模板: <ts_op/>(implied_volatility_call_<tenor/>/parkinson_volatility_<tenor/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore`, `ts_delta` | 时序操作 |
| `<tenor/>` | `120`, `270` | 期权期限 |
| `<d/>` | `66`, `126`, `252` | 窗口 |

---

### TPL-305: Put-Call成交量比
```
模板: <ts_op/>(pcr_vol_<tenor/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_delta`, `ts_zscore` | 时序操作 |
| `<tenor/>` | `10`, `30`, `60` | 期限 |
| `<d/>` | `22`, `66`, `126` | 窗口 |

---

### TPL-306: 期权盈亏平衡点
```
模板: group_rank(ts_zscore(<breakeven_field/>/close, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<breakeven_field/>` | `call_breakeven_10`, `put_breakeven_10` | 盈亏平衡字段 |
| `<d/>` | `66`, `126`, `252` | 窗口 |
| `<group/>` | `sector`, `industry` | 分组 |

---

## 第五部分：分析师类模板 (TPL-401 ~ TPL-420)

### TPL-401: 分析师预期变化
```
模板: <vec_op/>(tail(tail(<analyst_change_field/>, lower=<low/>, upper=<high/>, newval=<low/>), lower=-<high/>, upper=-<low/>, newval=-<low/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<vec_op/>` | `vec_avg`, `vec_sum` | 向量聚合 |
| `<analyst_change_field/>` | `oth41_s_west_eps_ftm_chg_3m`, `anl4_eps_chg` | 预期变化字段 |
| `<low/>` | `0.25`, `0.1` | 下截断值 |
| `<high/>` | `1000`, `100` | 上截断值 |

---

### TPL-402: 剥离动量的分析师因子
```
模板:
afr = <vec_op/>(<analyst_field/>);
short_mom = ts_mean(returns - group_mean(returns, 1, market), <d_short/>);
long_mom = ts_delay(ts_mean(returns - group_mean(returns, 1, market), <d_long/>), <d_long/>);
regression_neut(regression_neut(afr, short_mom), long_mom)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<vec_op/>` | `vec_avg`, `vec_sum` | 向量聚合 |
| `<analyst_field/>` | 分析师数据字段 | 一致预期等 |
| `<d_short/>` | `5`, `10` | 短期动量窗口 |
| `<d_long/>` | `20`, `22` | 长期动量窗口 |

---

### TPL-403: 分析师覆盖度过滤
```
模板:
coverage_filter = ts_sum(<vec_op/>(<analyst_field/>), <d/>) > <min_count/>;
if_else(coverage_filter, <alpha/>, nan)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<vec_op/>` | `vec_count` | 统计分析师数量 |
| `<analyst_field/>` | 分析师向量字段 | 分析师数据 |
| `<d/>` | `66`, `90`, `126` | 统计窗口 |
| `<min_count/>` | `2`, `3`, `5` | 最小覆盖数量 |
| `<alpha/>` | 主信号表达式 | 待过滤的Alpha |

---

### TPL-404: 老虎哥回归模板
```
模板: group_rank(ts_regression(ts_zscore(<field1/>, <d/>), ts_zscore(vec_sum(<field2/>), <d/>), <d/>), densify(sector))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field1/>` | 任意MATRIX字段 | Y变量 |
| `<field2/>` | 任意VECTOR字段 | X变量 |
| `<d/>` | `252`, `504` | 回归窗口 |

**说明**: 经典回归模板，适用于基本面与分析师数据组合

---

### TPL-405: 分析师预期时序变化
```
模板: ts_mean(vec_avg(<analyst_field/>), <d_short/>) - ts_mean(vec_avg(<analyst_field/>), <d_long/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<analyst_field/>` | `anl4_eps_mean`, `anl4_revenue_mean` | 分析师预测 |
| `<d_short/>` | `22`, `44` | 短期窗口 |
| `<d_long/>` | `66`, `126` | 长期窗口 |

---

### TPL-406: 三因子组合模板
```
模板:
my_group = market;
rank(
group_rank(ts_decay_linear(volume/ts_sum(volume, 252), 10), my_group) *
group_rank(ts_rank(vec_avg(<fundamental/>), <d/>), my_group) *
group_rank(-ts_delta(close, 5), my_group)
)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<fundamental/>` | 基本面VECTOR字段 | 基本面数据 |
| `<d/>` | `252`, `504` | 排名窗口 |

---

### TPL-407: 分析师FCF比率
```
模板: ts_rank(vec_avg(<fcf_field/>) / vec_avg(<profit_field/>), <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<fcf_field/>` | `anl4_fcf_value` | 自由现金流预测 |
| `<profit_field/>` | `anl4_netprofit_low`, `anl4_netprofit_mean` | 利润预测 |
| `<d/>` | `66`, `126`, `252` | 排名窗口 |

---

## 第六部分：中性化技术模板 (TPL-501 ~ TPL-515)

### TPL-501: 市值分组中性化
```
模板: group_neutralize(<alpha/>, bucket(rank(cap), range="<range/>"))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号表达式 | 待中性化的Alpha |
| `<range/>` | `"0.1,1,0.1"`, `"0,1,0.1"` | 分组范围 |

---

### TPL-502: 双重中性化 (行业+市值)
```
模板:
a1 = group_neutralize(<alpha/>, bucket(rank(cap), range="<range/>"));
group_neutralize(a1, <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<range/>` | `"0.1,1,0.1"` | 市值分组 |
| `<group/>` | `industry`, `sector`, `subindustry` | 行业分组 |

---

### TPL-503: 回归中性化
```
模板: regression_neut(<alpha/>, <factor/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<factor/>` | `log(cap)`, `ts_ir(returns, 126)`, `ts_std_dev(returns, 22)` | 待剥离因子 |

**多层回归中性化**:
```
模板: regression_neut(regression_neut(<alpha/>, <factor1/>), <factor2/>)
```

---

### TPL-504: 中性化顺序优化
```
模板:
a = ts_zscore(<field/>, <d/>);
a1 = group_neutralize(a, <group/>);
a2 = group_neutralize(a1, bucket(rank(cap), range="<range/>"))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意数据字段 | 主信号 |
| `<d/>` | `252` | zscore窗口 |
| `<group/>` | `industry`, `subindustry` | 行业分组 |
| `<range/>` | `"0.1,1,0.1"` | 市值分组 |

**说明**: 先行业中性化再市值中性化，与反向顺序效果可能不同

---

### TPL-505: sta1分组中性化
```
模板: group_neutralize(<alpha/>, sta1_top3000c20)
```
**说明**: 使用预定义的sta1分组进行中性化

---

## 第七部分：条件交易模板 (TPL-601 ~ TPL-620)

### TPL-601: 流动性过滤
```
模板: trade_when(volume > adv20 * <threshold/>, <alpha/>, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<threshold/>` | `0.618`, `0.5`, `1` | 流动性阈值 |
| `<alpha/>` | 主信号 | 原始Alpha |

**反向流动性**:
```
trade_when(volume < adv20, <alpha/>, -1)
```

---

### TPL-602: 波动率过滤
```
模板: trade_when(ts_rank(ts_std_dev(returns, <d1/>), <d2/>) < <threshold/>, <alpha/>, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d1/>` | `5`, `10`, `22` | 波动计算窗口 |
| `<d2/>` | `126`, `180`, `252` | 排名窗口 |
| `<threshold/>` | `0.8`, `0.9` | 波动率阈值 |
| `<alpha/>` | 主信号 | 原始Alpha |

---

### TPL-603: 极端收益过滤
```
模板: trade_when(abs(returns) < <entry/>, <alpha/>, abs(returns) > <exit/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<entry/>` | `0.075`, `0.05` | 入场阈值 |
| `<exit/>` | `0.1`, `0.095` | 出场阈值 |
| `<alpha/>` | 主信号 | 原始Alpha |

---

### TPL-604: 市值过滤
```
模板: trade_when(rank(cap) > <threshold/>, <alpha/>, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<threshold/>` | `0.3`, `0.5` | 市值排名阈值 |
| `<alpha/>` | 主信号 | 原始Alpha |

---

### TPL-605: 触发条件交易
```
模板:
triggerTradeexp = (ts_arg_max(volume, <d/>) < 1) && (volume > ts_sum(volume, <d/>)/<d/>);
triggerExitexp = -1;
trade_when(triggerTradeexp, <alpha/>, triggerExitexp)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d/>` | `5`, `10` | 判断窗口 |
| `<alpha/>` | `-rank(ts_delta(close, 2))` | 主信号 |

---

### TPL-606: 组合条件交易
```
模板:
my_group2 = bucket(rank(cap), range="0,1,0.1");
trade_when(volume > adv20, group_neutralize(<alpha/>, my_group2), -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 复合信号 | 主信号 |

---

### TPL-607: 条件排名交易
```
模板:
a = <ts_op/>(<field/>, <d/>);
trade_when(rank(a) > <threshold_low/>, -zscore(<field2/>)*a, <threshold_high/>-rank(a))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore` | 时序操作 |
| `<field/>` | 任意字段 | 条件字段 |
| `<field2/>` | 任意字段 | 信号字段 |
| `<d/>` | `25`, `66` | 窗口 |
| `<threshold_low/>` | `0.03`, `0.1` | 下阈值 |
| `<threshold_high/>` | `0.25`, `0.5` | 上阈值 |

---

## 第八部分：复合多因子模板 (TPL-701 ~ TPL-720)

### TPL-701: 三因子乘积
```
模板:
my_group = market;
rank(
group_rank(<ts_op1/>(<field1/>, <d1/>), my_group) *
group_rank(<ts_op2/>(<field2/>, <d2/>), my_group) *
group_rank(<ts_op3/>(<field3/>, <d3/>), my_group)
)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op1/>` | `ts_decay_linear`, `ts_rank` | 第一因子操作 |
| `<ts_op2/>` | `ts_rank`, `ts_zscore` | 第二因子操作 |
| `<ts_op3/>` | `-ts_delta` | 第三因子操作(反转) |
| `<field1/>` | `volume/ts_sum(volume, 252)` | 成交量趋势 |
| `<field2/>` | `vec_avg({Fundamental})` | 基本面信号 |
| `<field3/>` | `close` | 价格信号 |
| `<d1/>`, `<d2/>`, `<d3/>` | 各因子窗口 | 时间参数 |

---

### TPL-702: 波动率条件反转
```
模板:
vol = ts_std_dev(<ret_field/>, <d/>);
vol_mean = group_mean(vol, 1, market);
flip_ret = if_else(vol < vol_mean, -<ret_field/>, <ret_field/>);
-ts_mean(flip_ret, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ret_field/>` | `returns`, `close/open-1` | 收益字段 |
| `<d/>` | `20`, `22` | 窗口参数 |

**说明**: 低波动环境做反转，高波动环境做动量

---

### TPL-703: 恐惧指标组合
```
模板:
fear = ts_mean(
abs(returns - group_mean(returns, 1, market)) /
(abs(returns) + abs(group_mean(returns, 1, market)) + 0.1),
<d/>
);
-group_neutralize(fear * <signal/>, bucket(rank(cap), range="0.1,1,0.1"))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<d/>` | `20`, `22` | 恐惧指标窗口 |
| `<signal/>` | 主信号表达式 | 待组合信号 |

---

### TPL-704: 债务杠杆相关性
```
模板: group_neutralize(ts_zscore(<leverage_field/>, <d1/>) * ts_corr(<leverage_field/>, returns, <d2/>), sector)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<leverage_field/>` | `debt_to_equity`, `debt/assets` | 杠杆字段 |
| `<d1/>` | `60`, `126` | zscore窗口 |
| `<d2/>` | `20`, `66` | 相关性窗口 |

---

### TPL-705: 模型数据信号
```
模板: -<model_field/>
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<model_field/>` | `mdl175_01dtsv`, `mdl175_01icc` | 模型字段 |

**带排名版**:
```
rank(group_rank(ts_rank(ts_backfill(<model_field/>, 5), 5), sta1_top3000c20))
```

---

### TPL-706: 回归zscore模板
```
模板: ts_regression(ts_zscore(<field1/>, <d/>), ts_zscore(<field2/>, <d/>), <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field1/>` | MATRIX字段 | Y变量 |
| `<field2/>` | MATRIX字段或vec_sum(VECTOR) | X变量 |
| `<d/>` | `252`, `500`, `504` | 回归窗口 |

---

### TPL-707: 分组Delta模板
```
模板: group_neutralize(ts_delta(<field/>, <d/>), sector)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意数据字段 | 主字段 |
| `<d/>` | `22`, `66`, `126` | 差分窗口 |

---

## 第九部分：数据预处理模板 (TPL-801 ~ TPL-815)

### TPL-801: Winsorize截断
```
模板: winsorize(<field/>, std=<std/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 原始数据 |
| `<std/>` | `3`, `4`, `5` | 截断标准差 |

---

### TPL-802: Sigmoid归一化
```
模板: sigmoid(<ts_op/>(<field/>, <d/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_zscore`, `ts_ir`, `ts_rank` | 时序操作 |
| `<field/>` | 任意字段 | 原始数据 |
| `<d/>` | `22`, `66`, `252` | 窗口 |

---

### TPL-803: 数据回填
```
模板: ts_backfill(<field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 低频数据字段 | 需要回填的字段 |
| `<d/>` | `115`, `120`, `180`, `252` | 回填窗口 |

---

### TPL-804: 条件替换
```
模板: if_else(is_not_nan(<field/>), <field/>, <alternative/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 主字段 | 可能有NaN的字段 |
| `<alternative/>` | 替代字段或值 | NaN时的替代 |

---

### TPL-805: 极端值替换
```
模板: tail(tail(<field/>, lower=<low/>, upper=<high/>, newval=<low/>), lower=-<high/>, upper=-<low/>, newval=-<low/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 原始数据 |
| `<low/>` | `0.25`, `0.1` | 下界 |
| `<high/>` | `100`, `1000` | 上界 |

---

### TPL-806: 组合预处理
```
模板: <ts_op/>(winsorize(ts_backfill(<field/>, <d_backfill/>), std=<std/>), <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore`, `ts_mean` | 时序操作 |
| `<field/>` | 低频字段 | 需要处理的字段 |
| `<d_backfill/>` | `120`, `180` | 回填窗口 |
| `<std/>` | `4` | winsorize参数 |
| `<d/>` | `22`, `66` | 操作窗口 |

---

### TPL-807: ts_min/ts_max替代
```
模板: ts_backfill(if_else(ts_arg_min(<field/>, <d/>) == 0, <field/>, nan), 120)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 原始数据 |
| `<d/>` | `22`, `66`, `126` | 窗口 |

**说明**: 当ts_min/ts_max不可用时的替代方案

---

## 第十部分：高级统计模板 (TPL-901 ~ TPL-920)

### TPL-901: 高阶矩模板 (ts_moment)
```
模板: <ts_op/>(<group_op/>(ts_moment(<field/>, <d/>, k=<k/>), <group/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `rank`, `zscore`, `sigmoid` | 标准化操作 |
| `<group_op/>` | `group_rank`, `group_zscore` | 分组操作 |
| `<field/>` | 任意MATRIX字段 | 数据字段 |
| `<d/>` | `22`, `66`, `126` | 窗口 |
| `<k/>` | `2`, `3`, `4` | k=2方差, k=3偏度, k=4峰度 |

**说明**: ts_moment(x, d, k)计算k阶中心矩

---

### TPL-902: 协偏度/协峰度模板
```
模板: <group_op/>(ts_co_skewness(<field1/>, <field2/>, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<group_op/>` | `group_rank`, `group_zscore` | 分组操作 |
| `<field1/>` | `returns`, `close` | 第一变量 |
| `<field2/>` | `volume`, `vwap` | 第二变量 |
| `<d/>` | `66`, `126`, `252` | 窗口 |

**协峰度版**:
```
模板: <group_op/>(ts_co_kurtosis(<field1/>, <field2/>, <d/>), <group/>)
```

---

### TPL-903: 偏相关模板 (ts_partial_corr)
```
模板: group_rank(ts_partial_corr(<field1/>, <field2/>, <control/>, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field1/>` | `returns`, 收益相关 | Y变量 |
| `<field2/>` | 任意字段 | X变量 |
| `<control/>` | `group_mean(returns, 1, market)` | 控制变量(市场收益) |
| `<d/>` | `60`, `126`, `252` | 窗口 |
| `<group/>` | `sector`, `industry` | 分组 |

**说明**: 计算两变量偏相关，控制第三变量影响

---

### TPL-904: 三元相关模板 (ts_triple_corr)
```
模板: group_rank(ts_triple_corr(<field1/>, <field2/>, <field3/>, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field1/>` | `returns` | 第一变量 |
| `<field2/>` | `volume` | 第二变量 |
| `<field3/>` | 基本面字段 | 第三变量 |
| `<d/>` | `60`, `126` | 窗口 |
| `<group/>` | `sector`, `industry` | 分组 |

---

### TPL-905: Theil-Sen回归模板
```
模板: group_rank(ts_theilsen(<field1/>, <field2/>, <d/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field1/>` | 任意MATRIX字段 | Y变量 |
| `<field2/>` | 任意MATRIX字段或`ts_step(1)` | X变量 |
| `<d/>` | `126`, `252`, `500` | 窗口 |
| `<group/>` | `sector`, `industry` | 分组 |

**说明**: Theil-Sen回归比普通回归更鲁棒

---

### TPL-906: 多项式回归残差
```
模板: ts_poly_regression(<field1/>, <field2/>, <d/>, k=<k/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field1/>` | Y变量 | 被解释变量 |
| `<field2/>` | X变量 | 解释变量 |
| `<d/>` | `126`, `252` | 窗口 |
| `<k/>` | `1`, `2`, `3` | 多项式阶数, k=2为二次回归 |

**说明**: 返回 y - Ey (残差)

---

### TPL-907: 向量中性化模板
```
模板: ts_vector_neut(<alpha/>, <risk_factor/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 待中性化Alpha |
| `<risk_factor/>` | `returns`, `cap` | 风险因子 |
| `<d/>` | `22`, `66`, `126` | 窗口(不宜过长，计算慢) |

**分组向量中性化**:
```
模板: group_vector_neut(<alpha/>, <risk_factor/>, <group/>)
```

---

### TPL-908: 加权衰减模板
```
模板: group_neutralize(ts_weighted_decay(<alpha/>, k=<k/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 待衰减Alpha |
| `<k/>` | `0.3`, `0.5`, `0.7` | 衰减系数 |
| `<group/>` | `bucket(rank(cap), range="0.1,1,0.1")` | 分组 |

---

### TPL-909: 回归斜率模板
```
模板: ts_regression(ts_zscore(<field/>, <d/>), ts_step(1), <d/>, rettype=2)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意MATRIX字段 | 数据字段 |
| `<d/>` | `252`, `500` | 窗口 |

**说明**: rettype=2返回斜率，用于检测趋势

---

### TPL-910: 最小最大压缩模板
```
模板: ts_min_max_cps(<field/>, <d/>, f=<f/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<d/>` | `22`, `66`, `126` | 窗口 |
| `<f/>` | `2`, `0.5` | 压缩因子 |

**等价公式**: `x - f * (ts_min(x, d) + ts_max(x, d))`

---

## 第十一部分：事件驱动模板 (TPL-1001 ~ TPL-1020)

### TPL-1001: 数据变化天数模板
```
模板: if_else(days_from_last_change(<field/>) == <days/>, <alpha/>, nan)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 基本面字段 | 监测变化的字段 |
| `<days/>` | `1`, `2`, `5` | 距离变化的天数 |
| `<alpha/>` | `ts_delta(close, 5)`, 主信号 | 事件触发时的Alpha |

**动态衰减版**:
```
模板: <alpha/> / (1 + days_from_last_change(<field/>))
```

---

### TPL-1002: 最近差值模板
```
模板: <ts_op/>(last_diff_value(<field/>, <d/>), <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore` | 时序操作 |
| `<field/>` | 任意字段 | 数据字段 |
| `<d/>` | `60`, `90`, `120` | 回溯窗口 |
| `<d2/>` | `22`, `66` | 操作窗口 |

**说明**: 返回过去d天内最近一次不同于当前值的历史值

---

### TPL-1003: 缺失值计数模板
```
模板: -ts_count_nans(ts_backfill(<field/>, <d1/>), <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 分析师数据等 | 可能有缺失的字段 |
| `<d1/>` | `5`, `10` | 回填窗口 |
| `<d2/>` | `20`, `30` | 计数窗口 |

**应用**: 分析师覆盖度信号，缺失越少覆盖越好

---

### TPL-1004: 位置最大/最小模板
```
模板: if_else(ts_arg_max(<field/>, <d/>) == <position/>, <alpha/>, nan)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | `volume`, 任意字段 | 监测字段 |
| `<d/>` | `5`, `10` | 窗口 |
| `<position/>` | `0`, `1` | 0表示今天是最大值 |
| `<alpha/>` | 主信号 | 条件满足时的Alpha |

**组合条件**:
```
模板: (ts_arg_max(<field1/>, <d/>) == ts_arg_max(<field2/>, <d/>)) * (<alpha1/> + <alpha2/>)
```

---

### TPL-1005: 财报发布事件模板
```
模板:
event_signal = if_else(ts_delta(<fundamental_field/>, 1) != 0, <alpha/>, nan);
ts_decay_linear(event_signal, <decay_d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<fundamental_field/>` | `assets`, `sales`, `eps` | 基本面字段 |
| `<alpha/>` | `ts_delta(close, 5)`, 主信号 | 事件Alpha |
| `<decay_d/>` | `10`, `22` | 衰减窗口 |

---

### TPL-1006: 动态Decay事件驱动
```
模板:
decay_weight = 1 / (1 + days_from_last_change(<event_field/>));
<alpha/> * decay_weight
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<event_field/>` | 任意字段 | 事件触发字段 |
| `<alpha/>` | 主信号 | 原始Alpha |

---

### TPL-1007: 盈利公告模板
```
模板:
surprise = <actual_field/> - <estimate_field/>;
if_else(days_from_last_change(<actual_field/>) < <window/>, surprise, nan)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<actual_field/>` | `eps` | 实际值 |
| `<estimate_field/>` | `vec_avg(anl4_eps_mean)` | 预测值 |
| `<window/>` | `5`, `10` | 事件有效窗口 |

---

## 第十二部分：信号处理模板 (TPL-1101 ~ TPL-1120)

### TPL-1101: 黄金比例幂变换
```
模板: signed_power(<alpha/>, 0.618)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号表达式 | 原始Alpha |

**其他幂次**:
```
signed_power(<alpha/>, 0.5)   # 平方根
signed_power(<alpha/>, 2)     # 平方增强
```

---

### TPL-1102: 尾部截断模板
```
模板: right_tail(<alpha/>, minimum=<min/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<min/>` | `0`, `0.1` | 最小阈值 |

**左尾版**:
```
模板: left_tail(<alpha/>, maximum=<max/>)
```

---

### TPL-1103: Clamp边界限制
```
模板: clamp(<alpha/>, lower=<low/>, upper=<high/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<low/>` | `-1`, `-0.5` | 下界 |
| `<high/>` | `1`, `0.5` | 上界 |

---

### TPL-1104: 分数映射模板
```
模板: fraction(<alpha/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |

**说明**: 将连续变量映射到分布内的相对位置

---

### TPL-1105: NaN外推模板
```
模板: nan_out(<field/>, lower=<low/>, upper=<high/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<low/>` | `-3`, `-5` | 下界 |
| `<high/>` | `3`, `5` | 上界 |

**说明**: 将超出范围的值替换为NaN

---

### TPL-1106: Purify数据清洗
```
模板: purify(<field/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 需要清洗的数据 |

**说明**: 自动化数据清洗，减少噪声和异常值

---

### TPL-1107: 条件保留模板
```
模板: keep(<field/>, <condition/>, period=<d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<condition/>` | `<field/> > 0` | 保留条件 |
| `<d/>` | `3`, `5`, `10` | 滚动窗口 |

**示例**:
```
keep(returns, returns > 0, period=3)  # 只保留正收益
```

---

### TPL-1108: 缩放降维模板
```
模板: -scale_down(<ts_op/>(<field/>, <d1/>), constant=<c/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_mean`, `ts_rank` | 时序操作 |
| `<field/>` | `returns`, 任意字段 | 数据字段 |
| `<d1/>` | `2`, `5` | 窗口 |
| `<c/>` | `0.1`, `0.05` | 缩放常数 |

---

### TPL-1109: Truncate截断模板
```
模板: truncate(<alpha/>, maxPercent=<percent/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<percent/>` | `0.01`, `0.05` | 截断百分比 |

---

### TPL-1110: 组合Normalize模板
```
模板: group_normalize(<alpha/>, <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<group/>` | `sector`, `industry` | 分组 |

**等价公式**: `alpha / group_sum(abs(alpha), group)`

---

## 第十三部分：Turnover控制模板 (TPL-1201 ~ TPL-1215)

### TPL-1201: 目标换手率Hump
```
模板: ts_target_tvr_hump(<alpha/>, lambda_min=0, lambda_max=1, target_tvr=<target/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<target/>` | `0.1`, `0.15`, `0.2` | 目标换手率 |

---

### TPL-1202: Delta限制换手率
```
模板: ts_target_tvr_delta_limit(<alpha/>, <factor/>, lambda_min=0, lambda_max=1, target_tvr=<target/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<factor/>` | 辅助因子 | 限制因子 |
| `<target/>` | `0.1`, `0.15` | 目标换手率 |

---

### TPL-1203: Hump衰减组合
```
模板: hump_decay(<alpha/>, hump=<h/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<h/>` | `0.001`, `0.01` | Hump参数 |

**嵌套版**:
```
hump(hump_decay(<alpha/>, hump=0.001))
```

---

### TPL-1204: 平均+Hump模板
```
模板: -ts_mean(ts_target_tvr_hump(group_rank(<field/>, country), lambda_min=0, lambda_max=1, target_tvr=<target/>), <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<target/>` | `0.1` | 目标换手率 |
| `<d/>` | `5`, `10` | 平均窗口 |

---

### TPL-1205: 简单Hump模板
```
模板: hump(<alpha/>, hump=<h/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<h/>` | `0.01`, `0.001`, `0.0001` | Hump参数 |

**示例**:
```
hump(-ts_delta(close, 5), hump=0.01)
```

---

## 第十四部分：回填与覆盖模板 (TPL-1301 ~ TPL-1315)

### TPL-1301: 分组回填模板
```
模板: group_backfill(<field/>, <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 需要回填的字段 |
| `<group/>` | `sector`, `industry`, `market` | 分组字段 |

**说明**: 使用组内最近值填充NaN

---

### TPL-1302: 嵌套回填排名
```
模板: rank(group_backfill(<field/>, <group/>))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<group/>` | `sector`, `industry` | 分组 |

---

### TPL-1303: 覆盖度过滤
```
模板: group_count(is_nan(<field/>), market) > <threshold/> ? <alpha/> : nan
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 检测字段 |
| `<threshold/>` | `40`, `50` | 最小覆盖数 |
| `<alpha/>` | 主信号 | 原始Alpha |

---

### TPL-1304: NaN替换模板
```
模板: if_else(is_not_nan(<field/>), <field/>, <default/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<default/>` | `0`, `0.5`, `nan` | 默认值 |

---

### TPL-1305: 综合数据清洗
```
模板: <ts_op/>(winsorize(group_backfill(ts_backfill(<field/>, <d1/>), <group/>), std=<std/>), <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `ts_rank`, `ts_zscore` | 时序操作 |
| `<field/>` | 低频字段 | 数据字段 |
| `<d1/>` | `120`, `180` | 时序回填窗口 |
| `<group/>` | `sector`, `industry` | 分组回填 |
| `<std/>` | `4` | winsorize参数 |
| `<d2/>` | `66`, `126` | 操作窗口 |

---

## 第十五部分：组合提取模板 (TPL-1401 ~ TPL-1415)

### TPL-1401: group_extra填补模板
```
模板: group_extra(<field/>, <weight/>, <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<weight/>` | `0.5`, `1` | 权重 |
| `<group/>` | `densify(industry)`, `sector` | 分组 |

**说明**: 用组均值填补缺失值

---

### TPL-1402: 组合提取sigmoid
```
模板: scale(group_extra(ts_sum(sigmoid(ts_backfill(<field/>, <d1/>)), <d2/>) - ts_sum(sigmoid(ts_backfill(<field/>, <d1/>)), <d2/>), 0.5, densify(industry)))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<d1/>` | `180` | 回填窗口 |
| `<d2/>` | `3` | 求和窗口 |

---

### TPL-1403: PnL反馈模板
```
模板: if_else(inst_pnl(<alpha/>) > <threshold/>, <alpha/>, nan)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |
| `<threshold/>` | `0`, `-0.05` | PnL阈值 |

**说明**: 基于单标的PnL进行条件交易

---

### TPL-1404: 流动性加权模板
```
模板: <alpha/> * log(volume)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |

**说明**: 将仓位偏向高流动性股票

---

### TPL-1405: 市值回归中性化
```
模板: regression_neut(<alpha/>, log(cap))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<alpha/>` | 主信号 | 原始Alpha |

**说明**: 剥离市值因子影响

---

## 第十六部分：百分位与分位数模板 (TPL-1501 ~ TPL-1510)

### TPL-1501: 时序百分位模板
```
模板: ts_percentage(<field/>, <d/>, percentage=<p/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<d/>` | `22`, `66`, `126` | 窗口 |
| `<p/>` | `0.5`, `0.25`, `0.75` | 百分位 |

---

### TPL-1502: 分位数模板
```
模板: <ts_op/>(ts_quantile(<field/>, <d/>, <q/>), <d2/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ts_op/>` | `rank`, `zscore` | 标准化 |
| `<field/>` | 任意字段 | 数据字段 |
| `<d/>` | `66`, `126` | 窗口 |
| `<q/>` | `0.25`, `0.5`, `0.75` | 分位数 |
| `<d2/>` | `22` | 操作窗口 |

---

### TPL-1503: Max-Min比率模板
```
模板: ts_max_diff(<field/>, <d/>) / ts_av_diff(<field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<d/>` | `22`, `66` | 窗口 |

---

### TPL-1504: 中位数模板
```
模板: <field/> - ts_median(<field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<field/>` | 任意字段 | 数据字段 |
| `<d/>` | `22`, `66`, `252` | 窗口 |

---

### TPL-1505: 累积乘积模板
```
模板: ts_product(1 + <ret_field/>, <d/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<ret_field/>` | `returns`, 收益率字段 | 收益字段 |
| `<d/>` | `5`, `22`, `66` | 窗口 |

**说明**: 计算累积收益

---

## 第十七部分：实战表达式模板 (TPL-1601 ~ TPL-1700)

**说明**: 以下模板从社区高票帖子中提取，为实际验证过的表达式格式。

### TPL-1601: ts_max/ts_min替代公式
```
模板: {data} - ts_max_diff({data}, {d})                      # 等效于 ts_max
模板: (({data} - ts_max_diff({data}, {d})) * ts_scale({data}, {d}) - {data}) / (ts_scale({data}, {d}) - 1)  # 等效于 ts_min
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{data}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `22`, `66`, `126` | 窗口 |

**应用**: 当平台不支持ts_max/ts_min时的替代方案

---

### TPL-1602: 线性衰减权重公式
```
模板: weight = {d} + ts_step(0); ts_sum({data} * weight, {d}) / ts_sum(weight, {d})  # 等效于 ts_decay_linear
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{data}` | 任意字段 | 数据字段 |
| `{d}` | `10`, `22`, `66` | 衰减窗口 |

---

### TPL-1603: 组归一化公式
```
模板: {data} / group_sum(abs({data}), {group})  # 等效于 group_normalize
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{data}` | 任意字段 | 数据字段 |
| `{group}` | `industry`, `sector` | 分组字段 |

---

### TPL-1604: IR+峰度组合模板
```
模板:
rank_data = rank({field});
ts_ir(rank_data, {d}) + ts_kurtosis(rank_data, {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | `volume`, `returns`, 任意字段 | 数据字段 |
| `{d}` | `22`, `66` | 窗口 |

**说明**: IR和峰度组合捕捉信号强度和分布特征

---

### TPL-1605: VWAP相关性信号
```
模板: returns > -{threshold} ? (ts_ir(ts_corr(ts_returns(vwap, 1), ts_delay(group_neutralize({field}, market), {d1}), {d2}), {d2})) : -1
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意数据字段 | 信号字段 |
| `{threshold}` | `0.1`, `0.05` | 收益过滤阈值 |
| `{d1}` | `30`, `60` | 延迟窗口 |
| `{d2}` | `90`, `120` | 相关性窗口 |

---

### TPL-1606: 球队硬币因子 (ballteam_coin)
```
模板:
# 基础版
rank(ballteam_coin)

# 市值中性化版
group_neutralize(rank(ballteam_coin), bucket(rank(assets), range='0.1,1,0.1'))
```
**说明**: 经典球队vs硬币因子，用于捕捉收益持续性

---

### TPL-1607: 偏度因子模板
```
模板: -group_rank(ts_skewness(returns, {d}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `22`, `66`, `126` | 偏度计算窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 负偏度股票往往表现更好

---

### TPL-1608: 熵信号模板
```
模板: ts_zscore({field}, {d1}) * ts_entropy({field}, {d2})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | `returns`, 任意字段 | 信号字段 |
| `{d1}` | `14`, `22` | zscore窗口 |
| `{d2}` | `14`, `22` | 熵窗口 |

**说明**: 结合标准化和不确定性度量

---

### TPL-1609: 分析师动量短长差模板
```
模板: log(ts_mean(anl4_{data}_{stats}, {d_short})) - log(ts_mean(anl4_{data}_{stats}, {d_long}))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{data}` | `eps`, `revenue`, `netprofit` | 分析师预测类型 |
| `{stats}` | `mean`, `low`, `high` | 统计量类型 |
| `{d_short}` | `20`, `44` | 短期窗口 |
| `{d_long}` | `44`, `126` | 长期窗口 |

---

### TPL-1610: 目标换手率分组排名
```
模板: -ts_mean(ts_target_tvr_hump(group_rank({field}, country), lambda_min=0, lambda_max=1, target_tvr={target}), {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意字段 | 数据字段 |
| `{target}` | `0.1`, `0.15` | 目标换手率 |
| `{d}` | `5`, `10` | 平均窗口 |

---

### TPL-1611: 最大差/均值差比率
```
模板: ts_max_diff({field}, {d}) / ts_av_diff({field}, {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意字段 | 数据字段 |
| `{d}` | `22`, `66` | 窗口 |

**说明**: 捕捉极端值相对于平均变化的幅度

---

### TPL-1612: 模型数据三层嵌套
```
模板:
a = rank(group_rank(ts_rank(ts_backfill({model_field}, 5), 5), sta1_top3000c20));
trade_when(rank(a) > 0.03, -zscore(ts_zscore({model_field}, 25)) * a, 0.25 - rank(a))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{model_field}` | `mdl175_01icc`, `mdl175_01dtsv` | 模型字段 |

---

### TPL-1613: 量价触发条件交易
```
模板:
triggerTradeexp = (ts_arg_max(volume, {d}) < 1) && (volume > ts_sum(volume, {d}) / {d});
triggerExitexp = -1;
alphaexp = -rank(ts_delta(close, 2));
trade_when(triggerTradeexp, alphaexp, triggerExitexp)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `5`, `10` | 窗口 |

**说明**: 今日成交量为近期最大且高于均值时交易

---

### TPL-1614: 情绪成交量交易
```
模板:
sent_vol = vec_sum(scl12_alltype_buzzvec);
trade_when(rank(sent_vol) > 0.95, -zscore(scl12_buzz) * sent_vol, -1)
```
**说明**: 高情绪量时反向交易情绪

---

### TPL-1615: 双层中性化模板
```
模板:
a = ts_zscore({field}, 252);
a1 = group_neutralize(a, industry);
a2 = group_neutralize(a1, bucket(rank(cap), range='0.1,1,0.1'))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意字段 | 数据字段 |

**说明**: 先行业后市值的双重中性化

---

### TPL-1616: 相关性计算公式
```
模板:
a = {field1};
b = {field2};
p = {d};
c = ts_mean(ts_av_diff(a, p) * ts_av_diff(b, p), p);
c / ts_std_dev(a, p) / ts_std_dev(b, p)  # 近似 ts_corr
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field1}` | `close`, `returns` | 第一字段 |
| `{field2}` | `volume`, `open` | 第二字段 |
| `{d}` | `5`, `22` | 窗口 |

---

### TPL-1617: 回归中性化双因子
```
模板:
afr = vec_avg({analyst_field});
short_mom = ts_mean(returns - group_mean(returns, 1, market), {d_short});
long_mom = ts_delay(ts_mean(returns - group_mean(returns, 1, market), {d_long}), {d_long});
regression_neut(regression_neut(afr, short_mom), long_mom)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{analyst_field}` | 分析师VECTOR字段 | 分析师数据 |
| `{d_short}` | `5`, `10` | 短期动量窗口 |
| `{d_long}` | `20`, `22` | 长期动量窗口 |

**说明**: 剥离短期和长期动量后的分析师因子

---

### TPL-1618: 回归斜率趋势检测
```
模板: ts_regression(ts_zscore({field}, {d}), ts_step(1), {d}, rettype=2)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `252`, `500` | 窗口 |

**说明**: rettype=2返回回归斜率，检测长期趋势

---

### TPL-1619: 三因子乘积组合
```
模板:
my_group = market;
rank(
group_rank(ts_decay_linear(volume / ts_sum(volume, 252), 10), my_group) *
group_rank(ts_rank(vec_avg({fundamental}), {d}), my_group) *
group_rank(-ts_delta(close, 5), my_group)
)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{fundamental}` | 基本面VECTOR字段 | 基本面数据 |
| `{d}` | `252`, `504` | 排名窗口 |

**说明**: 成交量趋势 × 基本面排名 × 价格反转

---

### TPL-1620: 波动率条件反转
```
模板:
vol = ts_std_dev(returns, {d});
vol_mean = group_mean(vol, 1, market);
flip_ret = if_else(vol < vol_mean, -returns, returns);
-ts_mean(flip_ret, {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `20`, `22` | 窗口 |

**说明**: 低波动做反转，高波动做动量

---

### TPL-1621: 恐惧指标复合
```
模板:
fear = ts_mean(
abs(returns - group_mean(returns, 1, market)) /
(abs(returns) + abs(group_mean(returns, 1, market)) + 0.1),
{d}
);
-group_neutralize(fear * {signal}, bucket(rank(cap), range='0.1,1,0.1'))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `20`, `22` | 窗口 |
| `{signal}` | 主信号 | 待组合信号 |

---

### TPL-1622: 财务质量单因子
```
模板: group_neutralize(rank({fundamental_field}), bucket(rank(cap), range='0,1,0.1'))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{fundamental_field}` | `roe`, `roa`, `net_income/assets` | 财务质量指标 |

---

### TPL-1623: 老虎哥回归模板
```
模板: group_rank(ts_regression(ts_zscore({field1}, {d}), ts_zscore(vec_sum({field2}), {d}), {d}), densify(sector))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field1}` | 任意MATRIX字段 | Y变量 |
| `{field2}` | 任意VECTOR字段 | X变量 |
| `{d}` | `252`, `504` | 回归窗口 |

---

### TPL-1624: 综合数据清洗模板
```
模板: ts_decay_linear(-densify(zscore(winsorize(ts_backfill({field}, 115), std=4))), 10)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 低频字段如 `anl4_adjusted_netincome_ft` | 需要处理的字段 |

---

### TPL-1625: 延迟最大值位置模板
```
模板: ts_max({field}, {d}) = ts_delay({field}, ts_arg_max({field}, {d}))  # 等效公式
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意字段 | 数据字段 |
| `{d}` | `22`, `66` | 窗口 |

---

### TPL-1626: 数据探索通用模板
```
模板: zscore(ts_delta(rank(ts_zscore({field}, {d1})), {d2}))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 待探索数据字段 |
| `{d1}` | `60`, `126`, `252` | zscore窗口 |
| `{d2}` | `5`, `10`, `22` | delta窗口 |

**说明**: 顾问推荐的新数据探索模板，可替换op和时间参数

---

### TPL-1627: 自定义衰减权重模板
```
模板:
weight = {d} + ts_step(0);                       # 线性递增权重
ts_sum({data} * weight, {d}) / ts_sum(weight, {d})  # 加权平均

# 替代版 (ts_step递减)
ts_sum({alpha} * ts_step(1), {d}) / ts_sum(ts_step(1), {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{data}` | 任意字段 | 数据字段 |
| `{alpha}` | 主信号 | 原始Alpha |
| `{d}` | `10`, `22`, `66` | 衰减窗口 |

**说明**: 当没有ts_decay_linear权限时的替代方案

---

### TPL-1628: log_diff相对增长模板
```
模板: group_rank(log_diff({field}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 财务指标如 `sales`, `eps`, `assets` | 数据字段 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 检测相对增长率，对乘性变化更敏感

---

### TPL-1629: ts_product累积收益模板
```
模板: group_rank(ts_product(1 + {ret_field}, {d}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{ret_field}` | `returns`, 收益率字段 | 收益字段 |
| `{d}` | `22`, `66`, `126` | 窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 计算累积收益排名

---

### TPL-1630: ts_percentage阈值模板
```
模板:
high_threshold = ts_percentage({field}, {d}, percentage=0.5);
low_threshold = ts_percentage({field}, {d}, percentage=0.5);
{signal}
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | `close`, 价格字段 | 阈值计算字段 |
| `{d}` | `22`, `66` | 窗口 |
| `{signal}` | 主信号 | 条件信号 |

**说明**: 用于震荡带突破策略的阈值构建

---

### TPL-1631: 动量反转切换模板
```
模板:
mom = ts_sum(returns, {d_long}) - ts_sum(returns, {d_short});
reversal = -ts_delta(close, {d_short});
if_else(ts_rank(ts_std_dev(returns, {d_short}), {d_long}) > 0.5, mom, reversal)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d_short}` | `5`, `10` | 短期窗口 |
| `{d_long}` | `22`, `66` | 长期窗口 |

**说明**: 高波动环境用动量，低波动环境用反转

---

### TPL-1632: 市场收益率近似模板 (CHN)
```
模板:
value = rank(cap) > 0.9 ? cap : 0;
market_return = group_sum(returns * value, country) / group_sum(value, country);
market_return
```
**说明**: 用市值加权近似沪深300指数收益率，设置neutralization=NONE, decay=0

---

### TPL-1633: Beta回归中性化模板
```
模板:
market_return = group_mean(returns, 1, market);
ts_regression({field}, market_return, {d})  # 返回残差(Y - E[Y])
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 待中性化字段 |
| `{d}` | `126`, `252` | 回归窗口 |

**说明**: 使用一元线性回归剥离市场因子

---

### TPL-1634: ts_moment高阶矩k值模板
```
模板: ts_moment({field}, {d}, k={k})

k=2: 方差 (等价于 ts_std_dev^2)
k=3: 偏度 (等价于 ts_skewness)
k=4: 峰度 (等价于 ts_kurtosis)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `22`, `66`, `126` | 窗口 |
| `{k}` | `2`, `3`, `4` | 阶数 |

---

### TPL-1635: 龙头股因子增强模板
```
模板: sigmoid(rank(star_pm_global_rank))
```
**说明**: 对龙头股因子进行sigmoid增强

---

### TPL-1636: purify数据清洗嵌套模板
```
模板: group_rank(ts_rank(purify({field}), {d}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意字段 | 待清洗数据 |
| `{d}` | `22`, `66` | 排名窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: purify自动化清洗异常值和噪声

---

### TPL-1637: 理想振幅因子模板
```
模板:
amplitude = (high - low) / close;
ideal_amp = ts_percentage(amplitude, {d}, percentage=0.5);
group_rank(amplitude - ideal_amp, {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `22`, `66` | 百分位窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 实际振幅偏离理想振幅的程度

---

### TPL-1638: 异同离差乖离率因子 (MACD风格)
```
模板:
ema_short = ts_decay_exp_window({field}, {d_short}, 0.9);
ema_long = ts_decay_exp_window({field}, {d_long}, 0.9);
dif = ema_short - ema_long;
ts_zscore(dif, {d_signal})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | `close`, 价格字段 | 数据字段 |
| `{d_short}` | `12`, `22` | 短期EMA窗口 |
| `{d_long}` | `26`, `66` | 长期EMA窗口 |
| `{d_signal}` | `9`, `22` | 信号线窗口 |

---

### TPL-1639: 收益率条件筛选反转
```
模板:
high_ret = ts_rank(returns, {d1}) > 0.8;
low_ret = ts_rank(returns, {d1}) < 0.2;
if_else(high_ret, -returns, if_else(low_ret, returns, 0))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d1}` | `22`, `66` | 排名窗口 |

**说明**: 只对极端收益做反转

---

### TPL-1640: 三阶模板优化版
```
模板: <group_op/>(<ts_op1/>(<ts_op2/>(<field/>, <d1/>), <d2/>), <group/>)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `<group_op/>` | `group_rank`, `group_zscore` | 外层分组操作 |
| `<ts_op1/>` | `ts_rank`, `ts_delta`, `ts_mean` | 中层时序操作 |
| `<ts_op2/>` | `ts_zscore`, `ts_rank`, `ts_ir` | 内层时序操作 |
| `<field/>` | 任意字段 | 数据字段 |
| `<d1/>` | `60`, `126`, `252` | 内层窗口 |
| `<d2/>` | `5`, `22`, `66` | 外层窗口 |
| `<group/>` | `sector`, `industry` | 分组 |

**说明**: 经典三阶嵌套结构，可灵活替换各层操作符

---

### TPL-1641: ts_entropy信号检测模板
```
模板: ts_entropy({field}, {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | `returns`, `volume`, 任意MATRIX字段 | 数据字段 |
| `{d}` | `14`, `22`, `66` | 窗口 |

**说明**: 衡量时序数据的不确定性，高熵值表示更多随机性

---

### TPL-1642: 熵+ZScore组合模板
```
模板: ts_zscore({field}, {d}) * ts_entropy({field}, {d})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `14`, `22` | 窗口 |

**说明**: RSI超买超卖 + 熵不确定性组合，捕捉可能的修正

---

### TPL-1643: ts_ir+ts_entropy信号组合
```
模板:
signal = ts_ir({field}, {d}) + ts_entropy({field}, {d});
group_rank(signal, {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `22`, `66` | 窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: IR(信息比率)和Entropy组合捕捉信号稳定性和分布特征

---

### TPL-1644: trade_when市值过滤模板
```
模板: trade_when(rank(cap) > {threshold}, {alpha}, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{threshold}` | `0.3`, `0.5`, `0.7` | 市值排名阈值 |
| `{alpha}` | 主信号 | 原始Alpha |

**说明**: 仅交易大市值股票，降低prod corr

---

### TPL-1645: trade_when盈利过滤模板
```
模板: trade_when(eps > {threshold} * est_eps, group_rank((eps - est_eps)/est_eps, industry), -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{threshold}` | `1.0`, `1.1`, `1.2` | 盈利超预期比例 |

**说明**: 只交易盈利超预期的股票

---

### TPL-1646: trade_when量价触发模板
```
模板:
triggerTrade = (ts_arg_max(volume, {d}) < 1) && (volume > ts_sum(volume, {d})/{d});
trade_when(triggerTrade, {alpha}, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `5`, `10` | 判断窗口 |
| `{alpha}` | `-rank(ts_delta(close, 2))` | 主信号 |

**说明**: 量价突破触发条件交易

---

### TPL-1647: trade_when情绪量过滤模板
```
模板:
sent_vol = vec_sum({sentiment_vec});
trade_when(rank(sent_vol) > {threshold}, -zscore({sentiment_field}) * sent_vol, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{sentiment_vec}` | `scl12_alltype_buzzvec` 等VECTOR字段 | 情绪向量 |
| `{sentiment_field}` | `scl12_buzz`, `scl12_sentiment` | 情绪字段 |
| `{threshold}` | `0.9`, `0.95` | 情绪量阈值 |

**说明**: 高情绪量时反向交易情绪

---

### TPL-1648: bucket市值分组中性化模板
```
模板:
my_group2 = bucket(rank(cap), range='{range}');
group_neutralize({alpha}, my_group2)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{range}` | `'0,1,0.1'`, `'0.1,1,0.1'` | 分桶范围 |
| `{alpha}` | 主信号 | 原始Alpha |

**说明**: 按市值分桶进行中性化，去除规模效应

---

### TPL-1649: group_zscore时序组合模板
```
模板: group_zscore(ts_ir({field}, {d}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `22`, `66`, `126` | IR窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 在分组内进行IR的Z-score标准化

---

### TPL-1650: scale+rank+ts组合模板
```
模板: scale(rank(ts_zscore({field}, {d})))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `66`, `126`, `252` | 窗口 |

**说明**: 多层标准化处理信号

---

### TPL-1651: Betting Against Beta模板
```
模板:
market_return = group_mean(returns, 1, market);
beta = ts_regression(returns, market_return, {d}, rettype=2);
-group_rank(beta, industry)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `126`, `252` | 回归窗口 |

**说明**: 反Beta投注因子，做多低Beta股票

---

### TPL-1652: 跳跃因子模板
```
模板:
jump_up = ts_count(returns > ts_std_dev(returns, {d}) * {threshold}, {d});
jump_down = ts_count(returns < -ts_std_dev(returns, {d}) * {threshold}, {d});
group_rank(jump_down - jump_up, {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `22`, `66` | 统计窗口 |
| `{threshold}` | `2`, `2.5`, `3` | 标准差倍数 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 统计尾部跳跃事件的不对称性

---

### TPL-1653: 量小换手率模板
```
模板:
turnover = volume / sharesout;
low_turnover = ts_percentage(turnover, {d}, percentage=0.2);
group_rank(turnover < low_turnover, {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `22`, `66` | 百分位窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 识别低换手率状态

---

### TPL-1654: 隔夜收益因子模板
```
模板:
overnight_ret = open / ts_delay(close, 1) - 1;
group_rank(ts_mean(overnight_ret, {d}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `5`, `22`, `66` | 平均窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 隔夜"拉锯战"因子

---

### TPL-1655: sta1分组三因子模板
```
模板:
a = rank(group_rank(ts_rank(ts_backfill({field1}, {d1}), {d2}), sta1_top3000c20));
trade_when(rank(a) > {threshold}, -zscore(ts_zscore({field2}, {d3})) * a, {exit_threshold} - rank(a))
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field1}` | 任意字段 | 第一因子字段 |
| `{field2}` | 模型字段如`mdl175_01dtsv` | 第二因子字段 |
| `{d1}`, `{d2}`, `{d3}` | 各窗口参数 | 时间窗口 |
| `{threshold}` | `0.03`, `0.1` | 入场阈值 |
| `{exit_threshold}` | `0.25`, `0.5` | 出场阈值 |

**说明**: 使用sta1预定义分组的复合策略

---

### TPL-1656: macro泛化模板
```
模板: group_rank(ts_delta(ts_zscore({macro_field}, {d1}), {d2}), country)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{macro_field}` | 宏观数据字段 | 宏观数据 |
| `{d1}` | `126`, `252` | zscore窗口 |
| `{d2}` | `5`, `22` | delta窗口 |

**说明**: 基于Labs分析macro的泛化模板

---

### TPL-1657: ASI broker模板
```
模板:
signal = group_rank(ts_rank({broker_field}, {d}), market);
trade_when(volume > adv20, signal, -1)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{broker_field}` | broker数据字段 | 券商数据 |
| `{d}` | `22`, `66` | 排名窗口 |

**说明**: ASI区域broker因子，需设置max_trade=ON

---

### TPL-1658: Earnings超预期模板
```
模板:
surprise = (actual_eps - est_eps) / abs(est_eps);
group_rank(ts_zscore(surprise, {d}), industry)
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `66`, `126` | zscore窗口 |

**说明**: 盈利超预期因子

---

### TPL-1659: CCI技术指标模板
```
模板:
tp = (high + low + close) / 3;
cci = (tp - ts_mean(tp, {d})) / (0.015 * ts_mean(abs(tp - ts_mean(tp, {d})), {d}));
group_rank(-cci, {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{d}` | `14`, `20` | CCI窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 商品通道指数(CCI)反转策略

---

### TPL-1660: 0.618黄金比例幂变换模板
```
模板:
power_signal = signed_power({field}, 0.618);
group_rank(ts_zscore(power_signal, {d}), {group})
```
| 占位符 | 可选值 | 说明 |
|--------|--------|------|
| `{field}` | 任意MATRIX字段 | 数据字段 |
| `{d}` | `66`, `126` | zscore窗口 |
| `{group}` | `sector`, `industry` | 分组 |

**说明**: 使用黄金比例0.618进行幂次变换

---

## 附录A：标准时间窗口

| 窗口代号 | 天数 | 含义 |
|---------|------|------|
| `d_week` | 5 | 一周 |
| `d_month` | 22 | 一月 |
| `d_quarter` | 66 | 一季度 |
| `d_half` | 126 | 半年 |
| `d_year` | 252 | 一年 |
| `d_2year` | 504 | 两年 |

**使用规则**:
- 反转因子: 短窗口 `{3, 5, 22}`
- 动量因子: 中窗口 `{22, 66}`
- 长期趋势: 长窗口 `{126, 252, 504}`
- 回归/波动: 超长窗口 `{250, 500, 750}`

---

## 附录B：常用操作符分类

### 时序操作符 `<ts_op/>`
| 操作符 | 用途 |
|--------|------|
| `ts_mean` | 移动平均 |
| `ts_rank` | 时序排名 |
| `ts_delta` | 差分 |
| `ts_std_dev` | 移动标准差 |
| `ts_ir` | 信息比率 |
| `ts_zscore` | 时序Z-score |
| `ts_corr` | 滚动相关性 |
| `ts_regression` | 滚动回归 |
| `ts_decay_linear` | 线性衰减 |
| `ts_decay_exp_window` | 指数衰减 |
| `ts_sum` | 滚动求和 |
| `ts_backfill` | 数据回填 |
| `ts_arg_min` | 最小值位置 |
| `ts_arg_max` | 最大值位置 |
| `ts_max` | 滚动最大值 |
| `ts_min` | 滚动最小值 |
| `ts_delay` | 延迟 |
| `ts_moment` | k阶中心矩 |
| `ts_co_skewness` | 协偏度 |
| `ts_co_kurtosis` | 协峰度 |
| `ts_partial_corr` | 偏相关 |
| `ts_triple_corr` | 三元相关 |
| `ts_theilsen` | Theil-Sen回归 |
| `ts_poly_regression` | 多项式回归残差 |
| `ts_vector_neut` | 向量中性化 |
| `ts_weighted_decay` | 加权衰减 |
| `ts_min_max_cps` | 最小最大压缩 |
| `ts_max_diff` | 与最大值差 |
| `ts_av_diff` | 与均值差 |
| `ts_quantile` | 分位数 |
| `ts_percentage` | 百分位 |
| `ts_median` | 中位数 |
| `ts_product` | 累积乘积 |
| `ts_count_nans` | NaN计数 |
| `ts_scale` | 时序缩放 |
| `ts_target_tvr_hump` | 目标换手率Hump |
| `ts_target_tvr_delta_limit` | Delta换手率限制 |

### 分组操作符 `<group_op/>`
| 操作符 | 用途 |
|--------|------|
| `group_rank` | 分组排名 |
| `group_neutralize` | 分组中性化 |
| `group_zscore` | 分组Z-score |
| `group_mean` | 分组均值 |
| `group_sum` | 分组求和 |
| `group_extra` | 分组提取/填补 |
| `group_backfill` | 分组回填 |
| `group_normalize` | 分组归一化 |
| `group_vector_neut` | 分组向量中性化 |
| `group_vector_proj` | 分组向量投影 |
| `group_count` | 分组计数 |
| `group_std_dev` | 分组标准差 |

### 向量操作符 `<vec_op/>`
| 操作符 | 用途 |
|--------|------|
| `vec_avg` | 向量平均 |
| `vec_sum` | 向量求和 |
| `vec_max` | 向量最大 |
| `vec_min` | 向量最小 |
| `vec_stddev` | 向量标准差 |
| `vec_count` | 向量计数 |
| `vec_norm` | 向量归一化 |
| `vec_zscore` | 向量Z-score |
| `vec_range` | 向量范围 |

### 事件/时间操作符
| 操作符 | 用途 |
|--------|------|
| `days_from_last_change` | 距离上次变化天数 |
| `last_diff_value` | 最近不同值 |
| `ts_step` | 时间步长 |

### 信号处理操作符
| 操作符 | 用途 |
|--------|------|
| `signed_power` | 带符号幂变换 |
| `clamp` | 边界限制 |
| `left_tail` | 左尾截断 |
| `right_tail` | 右尾截断 |
| `fraction` | 分数映射 |
| `nan_out` | NaN外推 |
| `purify` | 数据清洗 |
| `keep` | 条件保留 |
| `scale_down` | 缩放降维 |
| `hump` | Hump平滑 |
| `hump_decay` | Hump衰减 |

### 其他常用操作符
| 操作符 | 用途 |
|--------|------|
| `rank` | 截面排名 |
| `zscore` | 截面Z-score |
| `sigmoid` | Sigmoid归一化 |
| `winsorize` | 极端值截断 |
| `truncate` | 截断 |
| `tail` | 尾部处理 |
| `scale` | 缩放 |
| `filter` | 过滤 |
| `densify` | 稠密化 |
| `bucket` | 分桶 |
| `log` | 对数 |
| `abs` | 绝对值 |
| `if_else` | 条件判断 |
| `trade_when` | 条件交易 |
| `regression_neut` | 回归中性化 |
| `regression_proj` | 回归投影 |
| `is_nan` | NaN检测 |
| `is_not_nan` | 非NaN检测 |
| `inst_pnl` | 单标的PnL |
| `convert` | 单位转换 |
| `pasteurize` | 去无效值 |

---

## 附录C：数据字段分类

### 量价类 `<pv_field/>`
```
close, open, high, low, vwap
returns, volume, adv20, sharesout, cap
```

### 基本面类 `<fundamental_field/>`
```
assets, sales, ebitda, net_income, eps, operating_income
goodwill, debt, cash, equity, gross_profit
fnd6_*, fnd72_*, mdl175_*, mdl163_*
debt_to_equity, roe, roa
```

### 分析师类 `<analyst_field/>` (VECTOR)
```
anl4_eps_mean, anl4_eps_low, anl4_eps_high
anl4_revenue_mean, anl4_fcf_value, anl4_netprofit_mean
anl4_adjusted_netincome_ft, anl4_bvps_flag
oth41_s_west_*, analyst_*
```

### 情绪类 `<sentiment_field/>`
```
scl12_sentiment, scl12_buzz, scl12_alltype_buzzvec
snt_value, snt_buzz, snt_buzz_ret, snt_buzz_bfl
nws18_relevance, nws18_ber
nws12_prez_result2, nws12_prez_short_interest
mws85_sentiment, mws46_mcv
```

### 期权类 `<option_field/>`
```
option8_*, option14_*
implied_volatility_call_120, implied_volatility_call_270
parkinson_volatility_120, parkinson_volatility_270
pcr_vol_10, pcr_vol_30
put_delta, call_delta, put_gamma, call_gamma
put_theta, call_theta, put_vega, call_vega
call_breakeven_10, put_breakeven_10
```

### 模型类 `<model_field/>`
```
mdl175_01dtsv, mdl175_01icc
mdl163_*, mdl*
```

### 分组类 `<group/>`
```
industry, sector, subindustry
market, country, exchange
sta1_top3000c20, sta1_*
pv13_*, pv27_*
```

"""

class SingleSession(requests.Session):
    _instance = None
    _lock = threading.Lock()
    _relogin_lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        if not self._initialized:
            super(SingleSession, self).__init__(*args, **kwargs)
            self._initialized = True

    def get_relogin_lock(self):
        return self._relogin_lock

def load_template_summary(file_path: Optional[str] = None) -> str:
    """
    Loads the template summary from a file or returns the built-in template summary.
    
    Args:
        file_path: Optional path to a .txt or .md file containing the template summary.
                   If None or file doesn't exist, returns the built-in template summary.
    
    Returns:
        str: The template summary content.
    """
    if file_path:
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists() and file_path_obj.is_file():
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✓ 成功从文件加载模板总结: {file_path}")
                    return content
            else:
                print(f"⚠ 警告: 文件不存在: {file_path}，将使用内置模板总结")
        except Exception as e:
            print(f"⚠ 警告: 读取文件时出错: {e}，将使用内置模板总结")
    
    # 返回内置的模板总结
    print("✓ 使用内置模板总结")
    return template_summary


def get_credentials() -> tuple[str, str]:
    """
    Retrieve or prompt for platform credentials.

    This function attempts to read credentials from a JSON file in the user's home directory.
    If the file doesn't exist or is empty, it prompts the user to enter credentials and saves them.

    Returns:
        tuple: A tuple containing the email and password.

    Raises:
        json.JSONDecodeError: If the credentials file exists but contains invalid JSON.
    """
    # 声明使用全局变量
    global username, password
    # please input your own BRAIN Credentials into the function
    return (username, password)

def get_token_from_auth_server() -> str:
    # 声明使用全局变量
    global LLM_API_KEY
    # please input your own LLM Gateway token into the function, please note, we are using kimi-k2.5 model
    return LLM_API_KEY

def interactive_input() -> dict:
    """
    交互式输入函数，收集所有必要的配置信息。
    
    Returns:
        dict: 包含所有配置信息的字典
    """
    print("\n" + "="*60)
    print("欢迎使用 Alpha Transformer 交互式配置")
    print("此程序在于让您输入一个Alpha ID即可通过历史总结的Alpha模板,转化成更多的表达式")
    print("72变,助您腾云驾雾")
    print("如果你想修改模型，则可以使用新模型的url和api key")
    print("不同模型效果不同，默认的kimi可能会产生语法错误，请检查生成的模板文件进行甄别")
    print("强烈推荐你使用自己总结的模板文档，效果会更好")
    print("="*60 + "\n")
    
    config = {}
    
    # 1. 询问 LLM 模型名称
    print("【1/6】LLM 模型配置")
    print("如果你想修改模型，则可以使用新模型的名称")
    default_model = "kimi-k2.5"
    model_input = input(f"请输入 LLM 模型名称 (直接回车使用默认值: {default_model}): ").strip()
    config['LLM_model_name'] = model_input if model_input else default_model
    print(f"✓ LLM 模型名称: {config['LLM_model_name']}\n")
    
    # 2. 询问 LLM API Key
    print("【2/6】LLM API Key 配置")
    api_key = getpass.getpass("请输入 LLM API Key (输入时不会显示): ").strip()
    if not api_key:
        print("⚠ 警告: API Key 为空，程序可能无法正常工作")
    config['LLM_API_KEY'] = api_key
    print("✓ API Key 已设置\n")
    
    # 3. 询问 LLM Base URL
    print("【3/6】LLM Base URL 配置")
    print("提示：不同模型有不同的URL")
    default_url = "https://api.moonshot.cn/v1"
    url_input = input(f"请输入 LLM Base URL (直接回车使用默认值: {default_url}): ").strip()
    config['llm_base_url'] = url_input if url_input else default_url
    print(f"✓ LLM Base URL: {config['llm_base_url']}\n")
    
    # 4. 询问 BRAIN 平台用户名
    print("【4/6】BRAIN 平台认证信息")
    username_input = input("请输入 BRAIN 平台用户名/邮箱: ").strip()
    if not username_input:
        print("⚠ 警告: 用户名为空，程序可能无法正常工作")
    config['username'] = username_input
    print("✓ 用户名已设置\n")
    
    # 5. 询问 BRAIN 平台密码
    password_input = getpass.getpass("请输入 BRAIN 平台密码 (输入时不会显示): ").strip()
    if not password_input:
        print("⚠ 警告: 密码为空，程序可能无法正常工作")
    config['password'] = password_input
    print("✓ 密码已设置\n")
    
    # 6. 询问模板总结文件路径
    print("【5/6】模板总结文件配置")
    print("强烈推荐你使用自己总结的模板文档，效果会更好")
    print("提示: 如果您有 template_summary 的 .txt 或 .md 文件，请输入完整路径")
    print("      如果没有，直接回车将使用内置模板总结")
    template_path = input("请输入模板总结文件路径 (直接回车使用内置模板): ").strip()
    config['template_summary_path'] = template_path if template_path else None
    if template_path:
        print(f"✓ 将尝试从文件加载: {template_path}\n")
    else:
        print("✓ 将使用内置模板总结\n")
    
    # 7. 询问 Alpha ID
    print("【6/7】Alpha ID 配置")
    alpha_id = input("请输入要处理的 Alpha ID: ").strip()
    if not alpha_id:
        print("❌ 错误: Alpha ID 不能为空")
        sys.exit(1)
    config['alpha_id'] = alpha_id
    print(f"✓ Alpha ID: {alpha_id}\n")
    
    # 8. 询问 Top N 参数（仅数据字段）
    print("【7/7】候选数量配置 (Top N)")
    print("提示: 此参数控制为每个占位符生成的数据字段候选数量")
    
    # Datafield top_n
    default_datafield_topn = 50
    datafield_topn_input = input(f"请输入数据字段候选数量 (直接回车使用默认值: {default_datafield_topn}): ").strip()
    try:
        config['top_n_datafield'] = int(datafield_topn_input) if datafield_topn_input else default_datafield_topn
    except ValueError:
        print(f"⚠ 警告: 输入无效，使用默认值: {default_datafield_topn}")
        config['top_n_datafield'] = default_datafield_topn
    print(f"✓ 数据字段候选数量: {config['top_n_datafield']}\n")
    
    print("="*60)
    print("配置完成！开始处理...")
    print("="*60 + "\n")
    
    return config



def expand_dict_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Expand dictionary columns in a DataFrame into separate columns.

    Args:
        data (pandas.DataFrame): The input DataFrame with dictionary columns.

    Returns:
        pandas.DataFrame: A new DataFrame with expanded columns.
    """
    dict_columns = list(filter(lambda x: isinstance(data[x].iloc[0], dict), data.columns))
    new_columns = pd.concat(
        [data[col].apply(pd.Series).rename(columns=lambda x: f"{col}_{x}") for col in dict_columns],
        axis=1,
    )

    data = pd.concat([data, new_columns], axis=1)
    return data

def start_session() -> SingleSession:
    """
    Start a new session with the WorldQuant BRAIN platform.

    This function authenticates the user, handles biometric authentication if required,
    and creates a new session.

    Returns:
        SingleSession: An authenticated session object.

    Raises:
        requests.exceptions.RequestException: If there's an error during the authentication process.
    """
    brain_api_url = "https://api.worldquantbrain.com"
    s = SingleSession()
    s.auth = get_credentials()
    r = s.post(brain_api_url + "/authentication")
    print(f"New session created (ID: {id(s)}) with authentication response: {r.status_code}, {r.json()} (新会话已创建)")
    if r.status_code == requests.status_codes.codes.unauthorized:
        if r.headers["WWW-Authenticate"] == "persona":
            print(
                "Complete biometrics authentication and press any key to continue (请完成生物识别认证并按任意键继续): \n"
                + urljoin(r.url, r.headers["Location"])
                + "\n"
            )
            input()
            s.post(urljoin(r.url, r.headers["Location"]))
            while True:
                if s.post(urljoin(r.url, r.headers["Location"])).status_code != 201:
                    input(
                        "Biometrics authentication is not complete. Please try again and press any key when completed (生物识别认证未完成，请重试并按任意键): \n"
                    )
                else:
                    break
        else:
            print("\nIncorrect email or password (邮箱或密码错误)\n")
            return start_session()
    return s

def get_data_categories(s: SingleSession) -> list[dict]:
    """
    Fetch and cache data categories from the BRAIN API.
    """
    global DATA_CATEGORIES
    if DATA_CATEGORIES is not None:
        return DATA_CATEGORIES
    
    try:
        brain_api_url = "https://api.worldquantbrain.com"
        response = s.get(brain_api_url + "/data-categories")
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            DATA_CATEGORIES = data
        elif isinstance(data, dict):
            DATA_CATEGORIES = data.get('results', [])
        else:
            DATA_CATEGORIES = []
        return DATA_CATEGORIES
    except Exception as e:
        print(f"Error fetching data categories: {e}")
        return []

def get_datafields(
    s: SingleSession,
    instrument_type: str = "EQUITY",
    region: str = "USA",
    delay: int = 1,
    universe: str = "TOP3000",
    theme: str = "false",
    dataset_id: str = "",
    data_type: str = "MATRIX",
    search: str = "",
    category: Union[str, list] = "",
) -> pd.DataFrame:
    """
    Retrieve available datafields based on specified parameters.

    Args:
        s (SingleSession): An authenticated session object.
        instrument_type (str, optional): The type of instrument. Defaults to "EQUITY".
        region (str, optional): The region. Defaults to "USA".
        delay (int, optional): The delay. Defaults to 1.
        universe (str, optional): The universe. Defaults to "TOP3000".
        theme (str, optional): The theme. Defaults to "false".
        dataset_id (str, optional): The ID of a specific dataset. Defaults to "".
        data_type (str, optional): The type of data. Defaults to "MATRIX".
        search (str, optional): A search string to filter datafields. Defaults to "".
        category (str or list, optional): A category ID or list of IDs to filter datafields. Defaults to "".

    Returns:
        pandas.DataFrame: A DataFrame containing information about available datafields.
    """
    brain_api_url = "https://api.worldquantbrain.com"
    type_param = f"&type={data_type}" if data_type != "ALL" else ""
    
    url_template = (
        brain_api_url
        + "/data-fields?"
        + f"&instrumentType={instrument_type}"
        + f"&region={region}&delay={str(delay)}&universe={universe}{type_param}&limit=50"
    )
    
    if dataset_id:
        url_template += f"&dataset.id={dataset_id}"
        
    if len(search) > 0:
        url_template += f"&search={search}"
        
    url_template += "&offset={x}"

    count = 0
    if len(search) == 0:
        try:
            count = s.get(url_template.format(x=0)).json()["count"]
        except Exception as e:
            print(f"Error getting count: {e}")
            return pd.DataFrame()
            
        if count == 0:
            print(
                f"No fields found (未找到字段): region={region}, delay={str(delay)}, universe={universe}, "
                f"type={data_type}, dataset.id={dataset_id}"
            )
            return pd.DataFrame()
    else:
        if category:
            count = 500 # Search deeper if filtering
        else:
            count = 100

    max_try = 5
    datafields_list = []
    found_count = 0
    target_found = 50 if category else count
    time.sleep(2)
    for x in range(0, count, 50):
        for _ in range(max_try):
            try:
                resp = s.get(url_template.format(x=x))
                while resp.status_code == 429:
                    print("status_code 429, sleep 3 seconds")
                    time.sleep(3)
                    resp = s.get(url_template.format(x=x))
                if resp.status_code == 200 and "results" in resp.json():
                    datafields = resp
                    break
            except:
                pass
            time.sleep(5)
        else:
            continue

        results = datafields.json().get("results", [])
        if not results:
            break
            
        if category:
            if isinstance(category, list):
                filtered_results = [
                    item for item in results 
                    if isinstance(item.get('category'), dict) and item['category'].get('id') in category
                ]
            else:
                filtered_results = [
                    item for item in results 
                    if isinstance(item.get('category'), dict) and item['category'].get('id') == category
                ]
            datafields_list.append(filtered_results)
            found_count += len(filtered_results)
            if len(search) > 0 and found_count >= target_found:
                break
        else:
            datafields_list.append(results)

    datafields_list_flat = [item for sublist in datafields_list for item in sublist]
    
    if not datafields_list_flat:
        return pd.DataFrame()

    datafields_df = pd.DataFrame(datafields_list_flat)
    datafields_df = expand_dict_columns(datafields_df)
    return datafields_df

def set_alpha_properties(
    s: SingleSession,
    alpha_id: str,
    name: Optional[str] = None,
    color: Optional[str] = None,
    regular_desc: Optional[str] = None,
    selection_desc: str = "None",
    combo_desc: str = "None",
    tags: Optional[list[str]] = None,
) -> requests.Response:
    """
    Update the properties of an alpha.

    Args:
        s (SingleSession): An authenticated session object.
        alpha_id (str): The ID of the alpha to update.
        name (str, optional): The new name for the alpha. Defaults to None.
        color (str, optional): The new color for the alpha. Defaults to None.
        regular_desc (str, optional): Description for regular alpha. Defaults to None.
        selection_desc (str, optional): Description for the selection part of a super alpha. Defaults to "None".
        combo_desc (str, optional): Description for the combo part of a super alpha. Defaults to "None".
        tags (list, optional): List of tags to apply to the alpha. Defaults to None.

    Returns:
        requests.Response: The response object from the API call.
    """
    brain_api_url = "https://api.worldquantbrain.com"
    params = {}
    if name is not None:
        params["name"] = name
    if color is not None:
        params["color"] = color
    if tags is not None:
        params["tags"] = tags
    if regular_desc is not None:
        params.setdefault("regular", {})["description"] = regular_desc
    if selection_desc != "None":  # Assuming "None" is the default string value for selection_desc
        params.setdefault("selection", {})["description"] = selection_desc
    if combo_desc != "None":  # Assuming "None" is the default string value for combo_desc
        params.setdefault("combo", {})["description"] = combo_desc
    
    response = s.patch(brain_api_url + "/alphas/" + alpha_id, json=params)

    return response


def extract_placeholders(template_expression: str) -> list[str]:
    """
    Extracts placeholders from a template expression using regular expressions.
    Placeholders are identified by text enclosed in angle brackets (e.g., `<data_field/>`).
    """
    # Only match placeholders of the form `<name/>` or `<name/>` with alphanumeric and underscores
    return re.findall(r'(<[A-Za-z0-9_]+/>)', template_expression)

def parse_alpha_code(alpha_code: str, all_operators: list[dict]) -> tuple[list[str], list[str]]:
    """
    Parses the alpha code to extract operators and data fields.
    """
    # Remove C-style comments /* ... */
    alpha_code = re.sub(r"/\*[\s\S]*?\*/", "", alpha_code)
    # Remove Python-style comments # ...
    alpha_code = re.sub(r"#.*", "", alpha_code)

    operators_names = [op['name'] for op in all_operators]
    
    found_operators = []
    found_datafields = []

    # Regex to find potential identifiers (operators or datafields)
    # This regex looks for words that could be operators or datafields,
    # excluding numbers and common programming constructs.
    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', alpha_code)

    for identifier in identifiers:
        if identifier in operators_names:
            found_operators.append(identifier)
        elif not (identifier.isdigit() or identifier.lower() in ['true', 'false', 'null', 'nan', 'if', 'else', 'for', 'while', 'return', 'and', 'or', 'not', 'in', 'is', 'try', 'except', 'finally', 'with', 'as', 'def', 'class', 'import', 'from', 'yield', 'lambda', 'global', 'nonlocal', 'break', 'continue', 'pass', 'async', 'await', 'raise', 'assert', 'del', 'print', 'input', 'len', 'min', 'max', 'sum', 'abs', 'round', 'int', 'float', 'str', 'list', 'dict', 'set', 'tuple', 'range', 'map', 'filter', 'zip', 'open', 'file', 'type', 'id', 'dir', 'help', 'object', 'super', 'issubclass', 'isinstance', 'hasattr', 'getattr', 'setattr', 'delattr', '__import__', 'None', 'True', 'False']):
            found_datafields.append(identifier)
            
    # Remove duplicates
    found_operators = list(set(found_operators))
    found_datafields = list(set(found_datafields))

    return found_operators, found_datafields

async def generate_alpha_description(alpha_id: str, brain_session: SingleSession) -> str:
    """
    Generates and potentially enriches the description of a given Alpha ID from the WorldQuant BRAIN API.

    Args:
        alpha_id (str): The ID of the alpha to retrieve.
        brain_session (SingleSession): The active BRAIN API session.
        llm_client (openai.AsyncOpenAI): The authenticated OpenAI-compatible client.

    Returns:
        str: A JSON string containing the alpha's settings, expression, and potentially enriched description,
             or an empty JSON string if an error occurs.
    """

    async def call_llm_new(prompt: str) -> dict:
        # 声明使用全局变量
        global LLM_model_name, LLM_API_KEY, llm_base_url
        try:
            llm_api_key = get_token_from_auth_server()
            llm_base_url_value = llm_base_url  # 使用全局变量
            llm_client = openai.AsyncOpenAI(base_url=llm_base_url_value, api_key=llm_api_key)
            print("LLM Gateway Authentication successful. (LLM网关认证成功)")
        except Exception as e:
            print(f"LLM Gateway Authentication failed (LLM网关认证失败): {e}")
            sys.exit(1)

        print("--- Calling LLM to propose templates... (正在调用LLM生成模板...) ---")
        try:
            # Await the async create call
            response = await llm_client.chat.completions.create(
                model=LLM_model_name,
                messages=[
                    {"role": "system", "content": "You are a quantitative finance expert and a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt},
                ],
                # response_format={"type": "json_object"},
            )

            # The async client may return a nested structure. Try to extract content robustly.
            content = None
            if isinstance(response, dict):
                # Some clients return raw dicts
                # Try common paths
                choices = response.get('choices')
                if choices and isinstance(choices, list):
                    msg = choices[0].get('message') or choices[0]
                    content = msg.get('content') if isinstance(msg, dict) else None
                elif 'content' in response:
                    content = response.get('content')
            else:
                # Fallback: attempt attribute access
                try:
                    content = response.choices[0].message.content
                except Exception:
                    content = None

            if content is None:
                # As a last resort, try to stringify the response
                content = str(response)

            # If content is already a dict/list, return it directly; if it's a JSON string, parse it.
            if isinstance(content, (dict, list)):
                return content
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Return wrapped string if not JSON
                    return {"text": content}

            return {}
        except Exception as e:
            print(f"Error calling LLM (调用LLM出错): {e}")
            return {}

    try:
        brain_api_url = "https://api.worldquantbrain.com"
        alpha_url = f"{brain_api_url}/alphas/{alpha_id}"
        response = brain_session.get(alpha_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        alpha_data = response.json()
        settings = alpha_data.get('settings', {})
        expression_dict = alpha_data.get('regular', alpha_data.get('combo', None))
        
        if not expression_dict or 'code' not in expression_dict:
            print(f"Error: Alpha expression code not found for Alpha ID (未找到Alpha表达式代码): {alpha_id}")
            return json.dumps({})

        alpha_code = expression_dict['code']
        current_description = expression_dict.get('description', '')

        # 1. Get all operators for parsing (no filter as per feedback)
        operators_data = get_brain_operators()
        all_operators = operators_data.get('operators', [])
        
        # 2. Parse the code to get operators and datafields
        found_operators_names, found_datafields_names = parse_alpha_code(alpha_code, all_operators)

        # 3. Get descriptions for operators
        operator_descriptions = {op['name']: op.get('description', 'No description available.') for op in all_operators if op['name'] in found_operators_names}
        
        # 4. Get descriptions for datafields
        datafield_descriptions = {}
        if found_datafields_names:
            # Extract settings from alpha_data for the get_datafields call
            instrument_type = settings.get('instrumentType', 'EQUITY')
            region = settings.get('region', 'USA')
            universe = settings.get('universe', 'TOP3000')
            delay = settings.get('delay', 1)

            for df_name in found_datafields_names:
                # get_datafields returns a DataFrame, so we need to process it
                datafield_df = get_datafields(s=brain_session, instrument_type=instrument_type, region=region, delay=delay, universe=universe, search=df_name)
                if not datafield_df.empty:
                    # Assuming the first result is the most relevant
                    datafield_descriptions[df_name] = datafield_df.iloc[0].get('description', 'No description available.')
                else:
                    datafield_descriptions[df_name] = 'No description found.'
                    
        # 5. Use LLM to judge if current description is good
        judgment_prompt = f"""
        Given the following alpha code, its current description, and descriptions of its operators and datafields:

        Alpha Code:
        {alpha_code}

        Current Description:
        {current_description}

        Operators and their descriptions:
        {json.dumps(operator_descriptions, indent=2)}

        Datafields and their descriptions:
        {json.dumps(datafield_descriptions, indent=2)}

        Alpha Settings:
        {json.dumps(settings, indent=2)}

        Is the current description good enough? Respond with 'yes' or 'no' in a JSON object: {{"judgment": "yes/no"}}
        A "good" description should clearly explain the investment idea, rationale for data used, and rationale for operators used.
        """
        
        judgment_response = await call_llm_new(judgment_prompt)
        is_description_good = judgment_response.get("judgment", "no").lower() == "yes"

        new_description = current_description
        if not is_description_good:
            # 6. If not good, use another LLM to generate a new description
            generation_prompt = f"""
            Based on the following alpha code, its operators, datafields, and settings, generate a new, improved description.
            The description should clearly explain the investment idea, rationale for data used, and rationale for operators used.
            Format the output as:
            "Idea: xxxxx\\nRationale for data used: xxxxx\\nRationale for operators used: xxxxxxx"

            Alpha Code:
            {alpha_code}

            Operators and their descriptions:
            {json.dumps(operator_descriptions, indent=2)}

            Datafields and their descriptions:
            {json.dumps(datafield_descriptions, indent=2)}

            Alpha Settings:
            {json.dumps(settings, indent=2)}
            """
            
            generated_description_response = await call_llm_new(generation_prompt)
            # Assuming LLM returns a string directly or a JSON with a 'description' key
            new_description = generated_description_response.get("description", generated_description_response)
            if isinstance(new_description, dict): # Handle cases where LLM might return a dict directly
                new_description = json.dumps(new_description, indent=2)

            # 7. Override this new description and patch the alpha
            set_alpha_properties(
                s=brain_session,
                alpha_id=alpha_id,
                regular_desc=new_description
            )
            print(f"Alpha {alpha_id} description updated on platform. (Alpha描述已在平台更新)")
            
        if 'regular' in alpha_data:
            alpha_data['regular']['description'] = new_description
        elif 'combo' in alpha_data:
            alpha_data['combo']['description'] = new_description

        return json.dumps({
            'settings': settings,
            'expression': expression_dict
        })

    except requests.exceptions.RequestException as e:
        print(f"Error during API request (API请求出错): {e}")
        return json.dumps({})
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from API. (无法解析API的JSON响应)")
        return json.dumps({})
    except Exception as e:
        print(f"An unexpected error occurred (发生意外错误): {e}")
        return json.dumps({})

def get_brain_operators(scope_filters: Optional[list[str]] = None) -> dict:
    """
    Retrieves the list of available operators from the WorldQuant BRAIN API,
    optionally filtered by a list of scopes. If no scopes are provided, all operators are returned.

    Args:
        scope_filters (list[str], optional): A list of strings to filter operators by their scope (e.g., ["REGULAR", "TS_OPERATOR"]).
                                             If None or empty, all operators are returned.

    Returns:
        dict: A dictionary containing the operators list and count,
              or an empty dictionary if an error occurs.
    """
    try:
        brain_api_url = "https://api.worldquantbrain.com"
        session = start_session()
        operators_url = f"{brain_api_url}/operators"
        response = session.get(operators_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        operators_list = response.json()
        
        if not isinstance(operators_list, list):
            print(f"Error: Expected a list of operators, but received type (预期运算符列表，但收到类型): {type(operators_list)}")
            return {}

        if scope_filters:
            filtered_operators = [
                op for op in operators_list
                if any(s_filter in op.get('scope', []) for s_filter in scope_filters)
            ]
            return {
                'operators': filtered_operators,
                'count': len(filtered_operators)
            }
        else:
            return {
                'operators': operators_list,
                'count': len(operators_list)
            }

    except requests.exceptions.RequestException as e:
        print(f"Error during API request for operators (获取运算符时API请求出错): {e}")
        return {}
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from operators API. (无法解析运算符API的JSON响应)")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while getting operators (获取运算符时发生意外错误): {e}")
        return {}

async def call_llm(prompt: str, llm_client: openai.AsyncOpenAI, max_retries: int = 3) -> dict:
    """
    Interface with a Large Language Model to process prompts and get a JSON response.
    Includes retry logic for JSON parsing errors.
    """
    # 声明使用全局变量
    global LLM_model_name
    if not llm_client:
        print("LLM client not initialized. Please check authentication. (LLM客户端未初始化，请检查认证)")
        return {}
    
    print("--- Calling LLM... (正在调用LLM...) ---")
    
    for attempt in range(max_retries):
        try:
            response = await llm_client.chat.completions.create(
                model=LLM_model_name,  # Or your preferred model
                messages=[
                    {"role": "system", "content": "You are a quantitative finance expert and a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt},
                ],
                # response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            
            # Try to clean markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠ JSON Decode Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"❌ Failed to parse JSON after {max_retries} attempts. Raw content: {content[:100]}...")
        except Exception as e:
            print(f"⚠ LLM Call Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"❌ Failed to call LLM after {max_retries} attempts.")
        
        # Wait before retrying
        await asyncio.sleep(2)
            
    return {}

async def propose_alpha_templates(alpha_details: dict, template_summary: str, llm_client: openai.AsyncOpenAI, user_data_type: str = "MATRIX") -> dict:
    """
    Uses an LLM to propose new alpha templates based on a seed alpha's details.

    Args:
        alpha_details (dict): The details of the seed alpha.
        template_summary (str): A summary of alpha templates to guide the LLM.
        llm_client (openai.AsyncOpenAI): The authenticated OpenAI-compatible client.
        user_data_type (str): The data type for the alpha (MATRIX or VECTOR).

    Returns:
        dict: A dictionary of proposed alpha templates in JSON format.
    """
    if not alpha_details.get('expression'):
        print("Error: Alpha expression is missing. (错误：缺少Alpha表达式)")
        return {}
    else:
        print(f"current seed alpha detail (当前种子Alpha详情): {alpha_details.get('expression')}")
    
    data_type_instruction = ""
    if user_data_type == "MATRIX":
        data_type_instruction = "\n**Important Note on Data Type:**\nThe user has specified the data type as **MATRIX**. Please do NOT use any vector-type operators (e.g., `vec_avg`, `vec_sum`) in your proposed templates, as they will raise errors for MATRIX type data in BRAIN. Note: 'MATRIX' is just a system identifier and does not refer to mathematical matrices."
    elif user_data_type == "VECTOR":
        data_type_instruction = "\n**Important Note on Data Type:**\nThe user has specified the data type as **VECTOR**. Please ensure you use vector-type operators (e.g., `vec_avg`, `vec_sum`) to handle the data fields before applying other operators."

    prompt = f"""
As a world-class BRAIN consultant, your task is to design new alpha templates based on an existing seed alpha.
You will be provided with the seed alpha's expression and a summary of successful alpha templates for inspiration.

**Seed Alpha Expression:**
{alpha_details['expression']}

**Inspiration: Summary of Alpha Templates:**
{template_summary}

**Your Task:**
Based on the structure and potential economic rationale of the seed alpha, by the aid of the Alpha template summary, propose 3-5 new, diverse alpha templates.

**Rules:**
1.  The proposed templates must be valid BRAIN alpha expressions.
2.  Use placeholders like `<data_field/>` for data fields and `<operator/>` for operators that can be programmatically replaced later.
3.  For each proposed template, provide a brief, clear explanation of its investment rationale.
4.  Return the output as a single, valid JSON object where keys are the proposed template strings and values are their corresponding explanations. Do not include any other text or formatting outside of the JSON object.
5.  The proposed new alpha template should be related to the economic sense of seed Alpha {alpha_details} but in different format such as. Utilize the inspiration well.
{data_type_instruction}

**Example Output Format:**
{{
  "<group_operators/>(<ts_operators/>(<data_field/>, 60), industry)": "A cross-sectional momentum signal, neutralized by industry, to capture relative strength within peer groups.",
  "<logical_operator/><ts_operators/>(<data_field/>, 20)": "A simple short-term momentum operator applied to a data field."
}}

Now, generate the JSON object with your proposed templates.
"""

    try:
        # print(f"现在的template summary是{template_summary}")
        proposed_templates = await call_llm(prompt, llm_client)
        return proposed_templates
    except Exception as e:
        print(f"An error occurred while calling the LLM (调用LLM时发生错误): {e}")
        return {}

async def propose_datafield_keywords(template_expression: str, template_explanation: str, placeholder: str, llm_client: openai.AsyncOpenAI, user_category: Optional[Union[str, list]] = None) -> list[str]:
    """
    Uses an LLM to propose search keywords for finding data fields.
    """
    category_instruction = ""
    if user_category:
        category_instruction = f"\n**User Specified Data Category:**\nThe user has specified the data category: {user_category}. Please ensure the proposed keywords are relevant to this category."
    else:
        category_instruction = "\n**Data Category:**\n Please propose keywords across diverse and relevant data categories."

    prompt = f"""
As a quantitative researcher, you need to find the best data fields for an alpha template placeholder.
Based on the template's logic and the placeholder's name, suggest a list of 3-5 concise search keywords to use with the WorldQuant BRAIN `get_datafields` tool.

**Alpha Template:**
`{template_expression}`

**Template Explanation:**
`{template_explanation}`

**Placeholder to Fill:**
`{placeholder}`
{category_instruction}

**Your Task:**
Provide a list of search keywords that are likely to yield relevant data fields for this placeholder. The keywords should be specific and diverse. Return the output as a single, valid JSON array of strings.

**Example Input:**
Placeholder: `<slow_moving_characteristic/>`
Explanation: "measures the time-series evolution of a fund's relative rank on a slow-moving characteristic (e.g., fund style, expense tier)"

**Example Output:**
["fund style", "expense ratio", "management fee", "turnover", "aum"]

    Now, generate the JSON array of search keywords for the given placeholder.
"""
    print(f"--- Calling LLM to get keywords for placeholder (正在调用LLM获取占位符关键词): {placeholder} ---")
    response = await call_llm(prompt, llm_client)
    print(f"AI使用如下提示词获取搜索关键词推荐：{prompt}")
    # Accept either a direct list or a dict containing a 'keywords' key
    if isinstance(response, list) and all(isinstance(item, str) for item in response):
        return response
    if isinstance(response, dict):
        # Common keys that might contain the list
        for key in ('keywords', 'data', 'result', 'items'):
            if key in response and isinstance(response[key], list) and all(isinstance(i, str) for i in response[key]):
                return response[key]
    print(f"Warning: LLM did not return a valid list of strings for keywords (警告：LLM未返回有效的关键词列表). Got: {response}")
    return []

async def get_datafield_candidates(s: SingleSession, alpha_details: dict, template_expression: str, template_explanation: str, placeholder: str, llm_client: openai.AsyncOpenAI, top_n: int = 50, user_region: Optional[str] = None, user_universe: Optional[str] = None, user_delay: Optional[int] = None, user_category: Optional[Union[str, list]] = None, user_data_type: str = "MATRIX") -> list[dict]:
    """
    Gets candidate data fields for a placeholder by using an LLM to generate search keywords
    and then calling the BRAIN API's get_datafields to retrieve the top N results for each keyword.
    """
    keywords = await propose_datafield_keywords(template_expression, template_explanation, placeholder, llm_client, user_category=user_category)
    if not keywords:
        print(f"Could not generate keywords for placeholder (无法生成占位符关键词): {placeholder}")
        return []

    print(f"LLM-proposed keywords for '{placeholder}' (LLM提议的关键词): {keywords}")

    # Extract settings from alpha_details for the get_datafields call
    settings = alpha_details.get('settings', {})
    print(f"Alpha settings for datafield search (用于数据字段搜索的Alpha设置):")
    instrument_type = settings.get('instrumentType', 'EQUITY')
    
    if user_region:
        region = user_region
    elif 'region' in settings:
        region = settings['region']
    else:
        print(f"❌ Error: Could not determine 'region' for datafield search. It is missing in Alpha settings and not provided by user. (错误：无法确定数据搜索的地区，Alpha设置中缺失且用户未提供)")
        return []
    print(f"   数据地区: {region}")
    
    if user_universe:
        universe = user_universe
    elif 'universe' in settings:
        universe = settings['universe']
    else:
        print(f"❌ Error: Could not determine 'universe' for datafield search. It is missing in Alpha settings and not provided by user. (错误：无法确定数据搜索的范围，Alpha设置中缺失且用户未提供)")
        return []
    print(f"   数据范围: {universe}")
    
    if user_delay is not None:
        delay = user_delay
    elif 'delay' in settings:
        delay = settings['delay']
    else:
        print(f"❌ Error: Could not determine 'delay' for datafield search. It is missing in Alpha settings and not provided by user. (错误：无法确定数据搜索的Delay，Alpha设置中缺失且用户未提供)")
        return []
    print(f"   Delay: {delay} 类别")
    
    if user_category:
        print(f"   Category Filter: {user_category}")

    # Use asyncio.gather to make parallel API calls for efficiency
    tasks = []
    for keyword in keywords:
        tasks.append(
            asyncio.to_thread(get_datafields,
                s=s,
                instrument_type=instrument_type,
                region=region,
                delay=delay,
                universe=universe,
                search=keyword,
                category=user_category if user_category else "",
                data_type=user_data_type
            )
        )
    
    results = await asyncio.gather(*tasks)

    # Process results to get top N from each keyword search
    top_results_per_keyword = []
    for res_df in results:
        if not res_df.empty:
            top_results_per_keyword.append(res_df.head(top_n))

    candidate_datafields = []
    if top_results_per_keyword:
        # Concatenate the top N results from all keywords
        combined_df = pd.concat(top_results_per_keyword, ignore_index=True)
        # Remove duplicates from the combined list
        combined_df.drop_duplicates(subset=['id'], inplace=True)
        # Format the final list of candidates
        candidate_datafields = combined_df[['id', 'description']].to_dict(orient='records')

    return candidate_datafields

async def get_group_datafield_candidates(template_expression: str, template_explanation: str, placeholder: str, llm_client: openai.AsyncOpenAI, top_n: int = 3) -> list[dict]:
    """
    Uses an LLM to select suitable group data fields from a predefined list.
    """
    predefined_group_fields = ["industry", "subindustry", "sector", "market", "exchange"]
    
    prompt = f"""
    As a quantitative researcher, you need to select the most relevant group data fields for an alpha template placeholder.
    Based on the template's logic and the placeholder's name, select {top_n} group fields from the following list that are most suitable: {predefined_group_fields}.
    
    **Alpha Template:**
    `{template_expression}`
    
    **Template Explanation:**
    `{template_explanation}`
    
    **Placeholder to Fill:**
    `{placeholder}`
    
    **Your Task:**
    Provide a list of selected group data fields. Return the output as a single, valid JSON array of strings.
    
    **Example Output Format:**
    ["industry", "sector"]
    
    Now, generate the JSON array of selected group data fields.
    """
    print(f"--- Calling LLM to select group datafields for placeholder (正在调用LLM选择分组数据字段): {placeholder} ---")
    response = await call_llm(prompt, llm_client)
    
    if isinstance(response, list) and all(isinstance(item, str) for item in response):
        return [{"name": field} for field in response[:top_n]]
    print(f"Warning: LLM did not return a valid list of strings for group datafields (警告：LLM未返回有效的分组数据字段列表). Got: {response}")
    return [{"name": field} for field in predefined_group_fields[:top_n]] # Fallback to default if LLM fails

async def get_operator_candidates(template_expression: str, template_explanation: str, placeholder: str, llm_client: openai.AsyncOpenAI, top_n: int = 3) -> list[dict]:
    """
    Gets candidate operators for a placeholder by first fetching all REGULAR scope operators
    and then using an LLM to select the most relevant ones.
    """
    operators_data = get_brain_operators(scope_filters=["REGULAR"])
    all_operators = operators_data.get('operators', [])

    if not all_operators:
        print("No REGULAR scope operators found. (未找到REGULAR范围的运算符)")
        return []

    # Create a summary of available operators for the LLM
    operator_names_and_descriptions = "\n".join([f"- {op['name']}: {op.get('description', 'No description available.')}" for op in all_operators])

    prompt = f"""
    As a quantitative finance expert, you need to select the most relevant operators for an alpha template placeholder.
    Based on the template's logic, its explanation, and the specific placeholder, select {top_n} operators from the provided list that are most suitable.

    **Alpha Template:**
    `{template_expression}`

    **Template Explanation:**
    `{template_explanation}`

    **Placeholder to Fill:**
    `{placeholder}`

    **Available REGULAR Scope Operators:**
    {operator_names_and_descriptions}

    **Your Task:**
    Provide a list of selected operator names. Return the output as a single, valid JSON array of strings.

    **Example Output Format:**
    ["ts_mean", "ts_rank", "ts_decay"]

    Now, generate the JSON array of selected operators.
    """
    print(f"--- Calling LLM to select operator candidates for placeholder (正在调用LLM选择运算符候选): {placeholder} ---")
    response = await call_llm(prompt, llm_client)

    if isinstance(response, list) and all(isinstance(item, str) for item in response):
        # Filter the full list of operators to return the selected ones with their descriptions
        selected_ops_details = []
        for selected_name in response:
            for op in all_operators:
                if op['name'] == selected_name:
                    selected_ops_details.append({"name": op['name'], "description": op.get('description', '')})
                    break
        return selected_ops_details[:top_n]
    
    print(f"Warning: LLM did not return a valid list of strings for operator candidates (警告：LLM未返回有效的运算符候选列表). Got: {response}")
    # Fallback to a default set if LLM fails
    return [{"name": op['name'], "description": op.get('description', '')} for op in all_operators[:top_n]]

async def get_parameter_candidates(param_type: str, template_expression: str, template_explanation: str, placeholder: str, llm_client: openai.AsyncOpenAI) -> list[dict]:
    """
    Uses an LLM to suggest sensible numerical candidates for parameters.
    """
    param_description = "an integer value, typically a window length or count (e.g., `d` in `ts_mean(x, d)`)" if param_type == "integer_parameter" else \
                        "a floating-point number, typically a threshold or factor"

    prompt = f"""
    As a quantitative finance expert, you need to suggest sensible numerical candidates for a placeholder parameter.
    Based on the alpha template's logic, its explanation, and the placeholder's type and context, propose 3-5 diverse numerical candidates.

    **Alpha Template:**
    `{template_expression}`

    **Template Explanation:**
    `{template_explanation}`

    **Placeholder to Fill:**
    `{placeholder}`

    **Parameter Type:**
    This placeholder represents {param_description}.

    **Your Task:**
    Provide a list of numerical candidates that are appropriate for this parameter. Return the output as a single, valid JSON array of numbers.

    **Example Output (for integer_parameter):**
    [10, 20, 60, 120, 252]

    **Example Output (for float_parameter):**
    [0.01, 0.05, 0.1, 0.2, 0.5]

    Now, generate the JSON array of numerical candidates.
    """
    print(f"--- Calling LLM to suggest candidates for {param_type} placeholder (正在调用LLM建议参数候选): {placeholder} ---")
    response = await call_llm(prompt, llm_client)

    if isinstance(response, list) and all(isinstance(item, (int, float)) for item in response):
        return [{"value": val} for val in response]
    print(f"Warning: LLM did not return a valid list of numbers for {param_type} candidates (警告：LLM未返回有效的数字候选列表). Got: {response}")
    
    # Fallback to default if LLM fails
    if param_type == "integer_parameter":
        return [{"value": x} for x in [10, 20, 60, 120, 252]]
    elif param_type == "float_parameter":
        return [{"value": x} for x in [0.01, 0.05, 0.1, 0.2, 0.5]]
    return []

async def judge_placeholder_type(placeholder: str, template_expression: str, template_explanation: str, operator_summary: str, llm_client: openai.AsyncOpenAI) -> str:
    """
    Uses an LLM to judge the type of placeholder (e.g., "data_field", "integer_parameter", "group_operator").
    """
    prompt = f"""
    As a world-class quantitative finance expert, your task is to classify the type of a placeholder within an alpha expression.
    You will be provided with the alpha template, its explanation, the specific placeholder, and a comprehensive summary of available BRAIN operators and data field characteristics.

    **Alpha Template:**
    `{template_expression}`

    **Template Explanation:**
    `{template_explanation}`

    **Placeholder to Classify:**
    `{placeholder}`

    **Available BRAIN Operators and Data Field Characteristics:**
    {operator_summary}

    **Your Task:**
    Classify the `{placeholder}` based on the provided context. The classification should be one of the following types:
    - "data_field": If the placeholder clearly represents a financial data series (e.g., price, volume, fundamental ratio).
    - "group_data_field": If the placeholder represents a categorical field used for grouping or neutralization (e.g., `industry` in `group_zscore(x, industry)`).
    - "operator": If the placeholder represents a BRAIN operator that performs a calculation or transformation.
    - "vector_operator": If the placeholder represents a vector operator (e.g., vec_avg, vec_sum).
    - "integer_parameter": If the placeholder represents an integer value, typically a window length or count (e.g., `d` in `ts_mean(x, d)`).
    - "float_parameter": If the placeholder represents a floating-point number, typically a threshold or factor.
    - "string_parameter": If the placeholder represents a string value, like a group name (e.g., `industry` in `group_zscore(x, industry)`).
    - "unknown": If the type cannot be determined from the context.

    Return the classification as a single JSON object with a key "placeholder_type" and its corresponding value. Do not include any other text or formatting outside of the JSON object.

    **Example Output Format:**
    {{"placeholder_type": "data_field"}}
    {{"placeholder_type": "integer_parameter"}}

    Now, classify the placeholder.
    """
    print(f"--- Calling LLM to judge type for placeholder (正在调用LLM判断占位符类型): {placeholder} ---")
    
    response = await call_llm(prompt, llm_client)
    return response.get("placeholder_type", "unknown")

async def populate_template(s: SingleSession, alpha_details: dict, template_expression: str, template_explanation: str, operator_summary: str, llm_client: openai.AsyncOpenAI, top_n_datafield: int = 50, user_region: Optional[str] = None, user_universe: Optional[str] = None, user_delay: Optional[int] = None, user_category: Optional[Union[str, list]] = None, user_data_type: str = "MATRIX") -> dict:
    """
    Populates placeholders in an alpha template with candidate data fields, operators, or parameters.
    """
    placeholders = extract_placeholders(template_expression)
    
    if not placeholders:
        print("No placeholders found in the template. (模板中未找到占位符)")
        return {}

    """
    Populates placeholders in an alpha template with candidate data fields, operators, or parameters.
    """
    placeholders = extract_placeholders(template_expression)
    print(f"Found placeholders in template (在模板中找到占位符): {placeholders}")
    
    populated_placeholders = {}

    for ph in placeholders:
        # Use LLM to judge placeholder type
        ph_type = await judge_placeholder_type(ph, template_expression, template_explanation, operator_summary, llm_client)
        print(f"'{ph}' judged as type (判断类型为): {ph_type}")

        if ph_type == "data_field":
            candidates = await get_datafield_candidates(s, alpha_details, template_expression, template_explanation, ph, llm_client, top_n=top_n_datafield, user_region=user_region, user_universe=user_universe, user_delay=user_delay, user_category=user_category, user_data_type=user_data_type)
            populated_placeholders[ph] = {"type": "data_field", "candidates": candidates}
        elif ph_type == "group_data_field":
            candidates = await get_group_datafield_candidates(template_expression, template_explanation, ph, llm_client)
            populated_placeholders[ph] = {"type": "group_data_field", "candidates": candidates}
        elif ph_type in ["operator", "group_operator", "ts_operator","vector_operator"]:
            candidates = await get_operator_candidates(template_expression, template_explanation, ph, llm_client)
            populated_placeholders[ph] = {"type": ph_type, "candidates": candidates}
        elif ph_type in ["integer_parameter", "float_parameter"]:
            candidates = await get_parameter_candidates(ph_type, template_expression, template_explanation, ph, llm_client)
            populated_placeholders[ph] = {"type": ph_type, "candidates": candidates}
        elif ph_type == "string_parameter":
            # Add logic for string_parameter if needed, for now it returns empty
            populated_placeholders[ph] = {"type": "string_parameter", "candidates": []}
        else:
            print(f"Could not determine type for placeholder (无法确定占位符类型): {ph} (LLM classified as {ph_type})")
            populated_placeholders[ph] = {"type": "unknown", "candidates": []}
            
    return populated_placeholders

def get_datafield_prefix(datafield_name: str) -> str:
    """Extracts the prefix from a datafield name (e.g., 'anl44_...' -> 'anl44')."""
    if '_' in datafield_name:
        return datafield_name.split('_')[0]
    return datafield_name

    

async def generate_new_alphas(alpha_description, brain_session, template_summary: Optional[str] = None, top_n_datafield: int = 50, user_region: Optional[str] = None, user_universe: Optional[str] = None, user_delay: Optional[int] = None, user_category: Optional[Union[str, list]] = None, user_data_type: str = "MATRIX"):
    """
    Main function to generate new alpha templates based on a seed alpha.
    
    Args:
        alpha_description: The alpha description JSON string.
        brain_session: The BRAIN session object.
        template_summary: Optional template summary string. If None, will load from built-in.
        top_n_datafield: Number of data field candidates to retrieve (default: 50).
        user_data_type: Data type for datafield search (MATRIX or VECTOR).
    """
    # 声明使用全局变量
    global LLM_model_name, LLM_API_KEY, llm_base_url
    
    # Load template summary if not provided
    if template_summary is None:
        template_summary = load_template_summary()
    # --- Load Operator Summary ---
    operator_summary = get_brain_operators(scope_filters=["REGULAR"])

    try:
        llm_api_key = get_token_from_auth_server()
        llm_base_url_value = llm_base_url  # 使用全局变量
        llm_client = openai.AsyncOpenAI(base_url=llm_base_url_value, api_key=llm_api_key)
        print("✓ LLM Gateway 认证成功")
    except Exception as e:
        print(f"❌ LLM Gateway 认证失败: {e}")
        sys.exit(1)

    details = json.loads(alpha_description)
    
    if not details:
        print(f"Failed to retrieve details for Alpha (获取Alpha详情失败)")
        sys.exit(1)
    
    print("Alpha Details Retrieved (已获取Alpha详情):")
    print(json.dumps(details, indent=4))


    # --- Step 4: Propose New Alpha Templates ---
    print(f"\n--- Proposing new alpha templates for Alpha (正在为Alpha提议新模板) ---")
    proposed_templates = await propose_alpha_templates(details, template_summary, llm_client, user_data_type=user_data_type)

    if not proposed_templates:
        print("Failed to generate proposed alpha templates. (生成提议模板失败)")
        sys.exit(1)
        
    print("\n--- Proposed Alpha Templates (JSON) (建议的Alpha模板,多样性会受到模型和模板总结文档的影响) ---")
    print(json.dumps(proposed_templates, indent=4))

    # --- Validation: Drop templates with suspicious literal identifiers ---
    try:
        operators_meta = get_brain_operators().get('operators', [])
        proposed_templates = _filter_valid_templates(
            proposed_templates,
            operators_meta,
            brain_session,
            details.get('settings', {}),
            parse_alpha_code,
        )
    except Exception as e:
        print(f"⚠ 模板校验步骤出现异常，跳过校验: {e}")

    if not proposed_templates:
        print("❌ 所有模板在校验后被丢弃，无法继续。")
        sys.exit(1)

    # --- Step 5: Process all proposed templates and gather candidates ---
    # --- Step 6: Prepare for Output ---
    # Ensure the output directory exists next to this script
    output_dir = Path(__file__).parent / "output"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: could not create directory {output_dir}: {e}")

    output_filepath = output_dir / f"Alpha_candidates.json"
    
    final_output = {}
    
    # --- Step 5: Process all proposed templates and gather candidates ---
    for template_expr, template_expl in proposed_templates.items():
        print(f"\n--- Populating template (正在填充模板): '{template_expr}' ---")
        try:
            populated_info = await populate_template(brain_session, details, template_expr, template_expl, operator_summary, llm_client, top_n_datafield=top_n_datafield, user_region=user_region, user_universe=user_universe, user_delay=user_delay, user_category=user_category, user_data_type=user_data_type)

            # Skip templates where any data_field placeholder has zero candidates
            if _should_skip_due_to_empty_candidates(populated_info):
                print("⚠ 该模板存在数据字段候选为空的占位符，跳过此模板。")
                continue
            
            final_output[template_expr] = {
                "template_explanation": template_expl,
                "seed_alpha_settings": details.get('settings', {}),
                "placeholder_candidates": populated_info
            }
            
            # --- Incremental Saving ---
            try:
                with output_filepath.open('w', encoding='utf-8') as f:
                    json.dump(final_output, f, indent=4)
                print(f"✓ Progress saved to {output_filepath.name}")
            except IOError as e:
                print(f"⚠️ Warning: Failed to save progress: {e}")
                
        except Exception as e:
            print(f"❌ Error processing template '{template_expr}': {e}")
            print("Skipping this template and continuing...")
            continue

    print("\n--- Final Consolidated Output (最终合并输出) ---")
    print(json.dumps(final_output, indent=4))


    generated_expressions = set()

    for template_expression, template_data in final_output.items():
        placeholder_candidates = template_data["placeholder_candidates"]
        seed_alpha_settings = template_data["seed_alpha_settings"]

        # Prepare a dictionary to hold lists of candidates for each placeholder
        candidates_for_placeholders = {}
        for placeholder, details in placeholder_candidates.items():
            # Extract only the 'value' or 'name' from the candidates list
            if details["type"] == "data_field":
                candidates_for_placeholders[placeholder] = [c["id"] for c in details["candidates"]]
            elif details["type"] in ["integer_parameter", "float_parameter"]:
                candidates_for_placeholders[placeholder] = [str(c["value"]) for c in details["candidates"]]
            elif details["type"] == "group_data_field":
                candidates_for_placeholders[placeholder] = [c["name"] for c in details["candidates"]]
            elif details["type"] == "operator":
                candidates_for_placeholders[placeholder] = [c["name"] for c in details["candidates"]]
            else:
                candidates_for_placeholders[placeholder] = []


        # --- Step 3: Implement logic to generate all alpha expression combinations from the candidates ---
        # Generate all possible combinations of placeholder values
        placeholder_names = list(candidates_for_placeholders.keys())
        all_combinations_values = list(itertools.product(*candidates_for_placeholders.values()))

        for combination_values in all_combinations_values:
            
            # --- ATOM Mode ---

            datafield_values_in_combo = []
            placeholder_types = {ph: details["type"] for ph, details in placeholder_candidates.items()}
            
            for i, placeholder_name in enumerate(placeholder_names):
                if placeholder_types.get(placeholder_name) == 'data_field':
                    datafield_values_in_combo.append(combination_values[i])
            
            if len(datafield_values_in_combo) > 1:
                first_prefix = get_datafield_prefix(datafield_values_in_combo[0])
                if not all(get_datafield_prefix(df) == first_prefix for df in datafield_values_in_combo):
                    continue  # Skip this combination as prefixes do not match

            current_expression = template_expression
            for i, placeholder_name in enumerate(placeholder_names):
                current_expression = current_expression.replace(placeholder_name, combination_values[i])
            
            # Check for duplicates before adding
            if current_expression not in generated_expressions:
                generated_expressions.add(current_expression)
    # dump all unique generated expressions to a file, a list of strings in json file
    print(f"\n--- Total Unique Generated Alpha Expressions (生成的唯一Alpha表达式总数): {len(generated_expressions)} ---")
    # output_filepath = output_dir / f"Alpha_generated_expressions.json"
    # try:
    #     with output_filepath.open('w', encoding='utf-8') as f:
    #         json.dump(list(generated_expressions), f, indent=4)
    #     print(f"\nGenerated expressions successfully written to {output_filepath} (生成的表达式已成功写入)")
    # except IOError as e:
    #     print(f"Error writing generated expressions to file {output_filepath} (写入生成的表达式出错): {e}")
    
    

    validator = val.ExpressionValidator()
    print("开始表达式语法检查感谢社区贡献，原帖https://support.worldquantbrain.com/hc/en-us/community/posts/36740689434391--check%E7%8E%8B-%E9%AA%8C%E8%AF%81%E8%A1%A8%E8%BE%BE%E5%BC%8F%E6%98%AF%E5%90%A6%E6%AD%A3%E7%A1%AE%E7%9A%84%E8%84%9A%E6%9C%AC-%E4%B8%83%E5%8D%81%E4%BA%8C%E5%8F%98%E9%BB%84%E9%87%91%E6%90%AD%E6%A1%A3?page=1#community_comment_36798176158999")
    print("请注意，该文件仅用于验证表达式的格式正确性，\n不保证表达式在实际使用中的逻辑正确性或可执行性。\n")
    print("不在内置函数列表中的operator将无法检查，如有需要，请使用AI按需修改本源代码添加")

    expressions_data = list(generated_expressions)
    # 提取表达式列表
    # 假设JSON文件结构为 {"expressions": ["expr1", "expr2", ...]} 或直接是 ["expr1", "expr2", ...]
    if isinstance(expressions_data, dict) and "expressions" in expressions_data:
        expressions = expressions_data["expressions"]
    elif isinstance(expressions_data, list):
        expressions = expressions_data
    else:
        print("错误: JSON文件格式不正确，需要包含表达式列表")
        return

    # 验证表达式
    valid_expressions = []
    invalid_expressions = []

    print(f"开始验证 {len(expressions)} 个表达式...")
    for i, expr in enumerate(expressions, 1):
        if i % 10 == 0:
            print(f"已验证 {i}/{len(expressions)} 个表达式")
            
        result = validator.check_expression(expr)
        if result["valid"]:
            valid_expressions.append(expr)
        else:
            invalid_expressions.append({"expression": expr, "errors": result["errors"]})

    # 生成输出文件路径
    name = "Alpha_generated_expressions"
    valid_output_path = os.path.join(output_dir, f"{name}_success.json")
    invalid_output_path = os.path.join(output_dir, f"{name}_error.json")

    # 保存结果到JSON文件
    print(f"\n验证完成！")
    print(f"有效表达式: {len(valid_expressions)}")
    print(f"无效表达式: {len(invalid_expressions)}")

    # 保存有效表达式
    try:
        with open(valid_output_path, 'w', encoding='utf-8') as f:
            json.dump(valid_expressions, f, ensure_ascii=False, indent=2)
        print(f"有效表达式已保存到: {valid_output_path}")
    except Exception as e:
        print(f"错误: 保存有效表达式失败 - {e}")

    # 保存无效表达式
    try:
        with open(invalid_output_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_expressions, f, ensure_ascii=False, indent=2)
        print(f"无效表达式已保存到: {invalid_output_path}，文件包含错误详情")
        print("查看该文件，你将获得修改模板的灵感，你可以定位到错误的模板并在APP里修改")
    except Exception as e:
        print(f"错误: 保存无效表达式失败 - {e}")

    print("请注意，该文件仅用于验证表达式的格式正确性，\n不保证表达式在实际使用中的逻辑正确性或可执行性。\n")
    print("不在内置函数列表中的operator将无法检查，如有需要，请使用AI按需修改validator源代码添加")

    print("不同模型效果不同，默认的kimi模型可能会产生Alpha语法错误，请检查生成的模板文件进行甄别")
    print("下一步，请下载已完成的模板，放入APP首页进行解析和语法检查，强烈建议生成表达式后手动尝试回测")


async def main():
    """
    Main execution function.
    """

    # Check for command line argument for config file
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✓ 已从命令行参数加载配置: {config_path}")
                # Ensure all required fields are present or set defaults
                if 'top_n_datafield' not in config:
                    config['top_n_datafield'] = 50
                if 'template_summary_path' not in config:
                    config['template_summary_path'] = None
            except Exception as e:
                print(f"❌ 加载配置文件失败: {e}")
                sys.exit(1)
        else:
            print(f"❌ 配置文件不存在: {config_path}")
            sys.exit(1)
    else:
        # --- Step 0: 交互式输入收集配置信息 ---
        print("输入回车加载同文件夹下的transformer_config.json文件，否则按其他任意键并回车，进入交互式输入账号信息")
        input_str = input()
        if input_str == "":
            config_path = os.path.join(os.path.dirname(__file__), 'transformer_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("\n" + "="*60)
            print("✓ 已从 transformer_config.json 加载账号配置")
            print("="*60 + "\n")
            
            # 继续交互式输入运行时参数
            # 1. 询问模板总结文件路径
            print("【1/3】模板总结文件配置")
            print("强烈推荐你使用自己总结的模板文档，效果会更好")
            print("提示: 如果您有 template_summary 的 .txt 或 .md 文件，请输入完整路径")
            print("      如果没有，直接回车将使用内置模板总结")
            template_path = input("请输入模板总结文件路径 (直接回车使用内置模板): ").strip()
            config['template_summary_path'] = template_path if template_path else None
            if template_path:
                print(f"✓ 将尝试从文件加载: {template_path}\n")
            else:
                print("✓ 将使用内置模板总结\n")
            
            # 2. 询问 Alpha ID
            print("【2/3】Alpha ID 配置")
            alpha_id = input("请输入要处理的 Alpha ID: ").strip()
            if not alpha_id:
                print("❌ 错误: Alpha ID 不能为空")
                sys.exit(1)
            config['alpha_id'] = alpha_id
            print(f"✓ Alpha ID: {alpha_id}\n")
            
            # 3. 询问 Top N 参数（仅数据字段）
            print("【3/3】候选数量配置 (Top N)")
            print("提示: 此参数控制为每个占位符生成的数据字段候选数量")
            default_datafield_topn = 50
            datafield_topn_input = input(f"请输入数据字段候选数量 (直接回车使用默认值: {default_datafield_topn}): ").strip()
            try:
                config['top_n_datafield'] = int(datafield_topn_input) if datafield_topn_input else default_datafield_topn
            except ValueError:
                print(f"⚠ 警告: 输入无效，使用默认值: {default_datafield_topn}")
                config['top_n_datafield'] = default_datafield_topn
            print(f"✓ 数据字段候选数量: {config['top_n_datafield']}\n")
            
            print("="*60)
            print("配置完成！开始处理...")
            print("="*60 + "\n")
        else:
            config = interactive_input()
    
    # 设置全局变量
    global LLM_model_name, LLM_API_KEY, llm_base_url, username, password
    LLM_model_name = config['LLM_model_name']
    LLM_API_KEY = config['LLM_API_KEY']
    llm_base_url = config['llm_base_url']
    username = config['username']
    password = config['password']
    
    # --- Step 1: 加载模板总结 ---
    template_summary = load_template_summary(config.get('template_summary_path'))
    
    # --- Step 2: 启动 BRAIN 会话 ---
    print("--- 正在启动 BRAIN 会话... ---")
    s = start_session()
    
    # --- Step 3: 认证 LLM Gateway ---
    llm_client = None
    print("--- 正在认证 LLM Gateway... ---")
    try:
        llm_api_key = get_token_from_auth_server()
        llm_base_url_value = llm_base_url
        llm_client = openai.AsyncOpenAI(base_url=llm_base_url_value, api_key=llm_api_key)
        print("✓ LLM Gateway 认证成功")
    except Exception as e:
        print(f"❌ LLM Gateway 认证失败: {e}")
        sys.exit(1)

    # --- Step 4: 获取 Alpha 详情 ---
    alpha_id = config['alpha_id']
    print(f"\n--- 正在获取 Alpha ID: {alpha_id} 的详情... ---")

    # --- Step 4.5: 交互式选择数据字段范围 ---
    if len(sys.argv) > 1:
         user_datafield_config = {
            'user_region': config.get('user_region'),
            'user_universe': config.get('user_universe'),
            'user_delay': config.get('user_delay'),
            'user_category': config.get('user_category'),
            'user_data_type': config.get('user_data_type', 'MATRIX')
        }
    else:
        user_datafield_config = interactive_datafield_selection(s)

    details_str = await generate_alpha_description(alpha_id, brain_session=s)
    await generate_new_alphas(
        alpha_description=details_str, 
        brain_session=s, 
        template_summary=template_summary,
        top_n_datafield=config.get('top_n_datafield', 50),
        user_region=user_datafield_config.get('user_region'),
        user_universe=user_datafield_config.get('user_universe'),
        user_delay=user_datafield_config.get('user_delay'),
        user_category=user_datafield_config.get('user_category'),
        user_data_type=user_datafield_config.get('user_data_type', 'MATRIX')
    )
    
def interactive_datafield_selection(s: SingleSession) -> dict:
    """
    Interactively ask the user for datafield search configuration (Region, Universe, Delay).
    """
    print("\n" + "="*60)
    print("【附加配置】数据字段搜索范围配置")
    print("正在获取有效的 Region/Universe/Delay 组合...")
    
    try:
        df = get_instrument_type_region_delay(s)
    except Exception as e:
        print(f"⚠ 获取配置选项失败: {e}")
        print("将使用 Seed Alpha 的默认设置")
        return {}

    # Filter for EQUITY only as per current logic
    df_equity = df[df['InstrumentType'] == 'EQUITY']
    
    if df_equity.empty:
        print("未找到 EQUITY 类型的配置选项。")
        return {}
        
    # 1. Select Region
    regions = df_equity['Region'].unique().tolist()
    print(f"\n可用地区 (Region): {regions}")
    region_input = input(f"请输入地区 (直接回车使用 Seed Alpha 默认值): ").strip()
    
    selected_region = None
    if region_input:
        if region_input in regions:
            selected_region = region_input
        else:
            print(f"⚠ 输入无效，将使用默认值")
    
    # 2. Select Delay
    # If region is selected, filter delays for that region
    if selected_region:
        delays = df_equity[df_equity['Region'] == selected_region]['Delay'].unique().tolist()
    else:
        delays = df_equity['Delay'].unique().tolist()
        
    print(f"\n可用延迟 (Delay): {delays}")
    delay_input = input(f"请输入延迟 (直接回车使用 Seed Alpha 默认值): ").strip()
    
    selected_delay = None
    if delay_input:
        try:
            d_val = int(delay_input)
            if d_val in delays:
                selected_delay = d_val
            else:
                print(f"⚠ 输入不在列表中，将使用默认值")
        except ValueError:
            print(f"⚠ 输入无效，将使用默认值")

    # 3. Select Universe
    # If region and delay are selected, filter universes
    if selected_region and selected_delay is not None:
        subset = df_equity[(df_equity['Region'] == selected_region) & (df_equity['Delay'] == selected_delay)]
        if not subset.empty:
            universes = subset.iloc[0]['Universe']
        else:
            universes = []
    else:
        # Just show all unique universes if we can't filter precisely
        universes = set()
        for u_list in df_equity['Universe']:
            universes.update(u_list)
        universes = list(universes)
        
    print(f"\n可用范围 (Universe): {universes}")
    universe_input = input(f"请输入范围 (直接回车使用 Seed Alpha 默认值): ").strip()
    
    selected_universe = None
    if universe_input:
        if universe_input in universes:
            selected_universe = universe_input
        else:
             print(f"⚠ 输入无效，将使用默认值")
             
    # 4. Select Category
    print("\n正在获取数据类别 (Data Categories)...")
    categories = get_data_categories(s)
    
    selected_category = None
    if categories:
        print("\n可用类别 (Categories):")
        for i, cat in enumerate(categories):
            print(f"{i+1}. {cat['name']} (ID: {cat['id']})")
            
        cat_input = input(f"请输入类别编号或ID (多个用逗号分隔, 直接回车不筛选): ").strip()
        
        if cat_input:
            selected_categories = []
            inputs = [x.strip() for x in cat_input.split(',')]
            
            for inp in inputs:
                # Check if input is an index
                if inp.isdigit():
                    idx = int(inp) - 1
                    if 0 <= idx < len(categories):
                        selected_categories.append(categories[idx]['id'])
                        print(f"已选择类别: {categories[idx]['name']}")
                else:
                    # Check if input is an ID
                    found = False
                    for cat in categories:
                        if cat['id'] == inp:
                            selected_categories.append(cat['id'])
                            print(f"已选择类别: {cat['name']}")
                            found = True
                            break
                    if not found:
                        print(f"⚠ 输入无效: {inp}")
            
            if selected_categories:
                selected_category = selected_categories
            else:
                print(f"⚠ 未选择有效类别，将不筛选类别")
    else:
        print("⚠ 无法获取类别列表，跳过类别选择")

    # 5. Select Data Type
    print("\n可用数据类型 (Data Type): [MATRIX, VECTOR]")
    data_type_input = input(f"请输入数据类型 (直接回车默认 MATRIX): ").strip().upper()
    
    selected_data_type = "MATRIX"
    if data_type_input == "VECTOR":
        print("⚠ 警告: 请确保您输入的原型Alpha中正确地使用了vector operator,否则极容易造成数据类型错误")
        confirm = input("确认使用 VECTOR 吗? (y/n): ").strip().lower()
        if confirm == 'y':
            selected_data_type = "VECTOR"
        else:
            print("已取消 VECTOR 选择，使用默认值 MATRIX")
    elif data_type_input and data_type_input != "MATRIX":
        print(f"⚠ 输入无效，将使用默认值 MATRIX")

    return {
        'user_region': selected_region,
        'user_universe': selected_universe,
        'user_delay': selected_delay,
        'user_category': selected_category,
        'user_data_type': selected_data_type
    }

if __name__ == "__main__":
    # To allow asyncio to run in environments like Jupyter notebooks
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

