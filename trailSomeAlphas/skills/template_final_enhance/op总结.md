先给个小计划：
1）用一个统一的单因子例子（比如 anl11_esgreg_industryperc）来思考“哪些区间有信号、哪些是噪音”。
2）按运算符类别，一一说明典型适用场景，重点围绕你提到的“只一部分区间有信号 / 极值是噪音 / 时序更重要”等情况。

下面我按类别来梳理，每个只讲“什么时候应该想起它”。

一、简单算术类（add / subtract / multiply / reverse / power / signed_power / log / sqrt / s_log_1p / abs）

add(A, c) / subtract(A, c)

场景：想把阈值移动到别的区间，例如 A 本来 0–100，你想用 “(A-50)>0” 判断高于中位；
简单平移，用于配合逻辑运算符（greater/less）做“高于某个基准”的判断。
multiply(A, c)（c>0）

场景：你已经认可当前形状/排序，只想调整“力度”（控制尾部放大还是压缩）或和其他因子对齐量级；
调权重，不改变好坏排序。
reverse(A)（-A）

场景：你发现指标“值越小越好”（比如利差、成本），想改成“值越大越好”的方向；
或同一个原始字段想同时挖 value/momentum 两方向信号，一个用 A，一个用 -A。
power(A, y)（A≥0）

场景：你希望放大高端或低端：
y>1：突出极端高值（比如只关心极高 ESG 的公司—tail 强调）；
0<y<1：压缩差距，只保留大致排序，不让极端值太主导。

signed_power(A, y)
场景：A 有正负，正负号本身有含义（好/坏），你只想“非线性放大极端程度”，不能把符号毁掉；
比如盈利 surprise zscore，高正/高负都想被放大，而 0 附近缩小。
log(A) / sqrt(A)（A>0）

场景：A 分布高度右偏，极个别超大值是噪音，想压扁右尾；
例如成交量类、规模类字段拉得太长，用 log 把大公司压回来，但顺序还保留。
s_log_1p(A)

场景：想把正负两边都压短，但不破坏“正是好、负是坏”的结构；
尤其适用于 zscore 后的因子，避免少数极端 zscore>5 的点主导。
abs(A)

场景：你不在乎正负方向，只关心“离中性多远”：
如“极端 ESG 无论好坏都可能带来风险溢价”，先做 zscore，再 abs 找两端。
二、逻辑运算符（greater / less / greater_equal / less_equal / equal / not_equal / and / or / not / if_else / is_nan / trade_when）

greater(A, threshold) / less(A, threshold)

场景：你认为只有高于某阈值的区域才有信号，中间区间全是噪音；
如：greater(A, 80) 把 ESG 行业分位 >80% 的打上标签。
if_else(cond, x, y)

场景：要做“分段函数”：
例如 A>80 用 A 自己，A 在 20–80 之间直接给 0，A<20 用 -A；
用来实现“头尾有含义，中间视为 0”。
trade_when(cond, new_value, old_value)

场景：你想在满足条件时改变 alpha 值 / 关闭仓位：
如：trade_when(less(A,20), NAN, A) → 低于 20 分的 ESG 直接不持仓；
或只在 “A 显著好/差” 时 trade，其他时间保持昨天的权重。
and / or / not

场景：组合多条件，例如“ESG 高且 盈利高 才算好”，“ESG 差或 盈利差 就算差”；
在你刚才举的 ESG×盈利例子、区间过滤里非常关键。
is_nan(A)

场景：处理缺失数据，过滤掉“看似极值其实是缺数据”的点；
或建立“有无披露”的信号（披露本身可能有含义）。
三、截面预处理&形状控制（winsorize / zscore / normalize / quantile / truncate / scale）

winsorize(A, std=4)

场景：你怀疑极小区间（最极端头/尾）是噪音，但又不想完全扔掉：
用标准差裁剪，把极值“拉回”可控范围，保留排序；
如 ESG 分数里个别公司数据错误/极端，先 winsorize 再用。
zscore(A)

场景：
你想把不同尺度的指标放到统一标准（利于后续组合或理解强度）；
或直接用 “相对平均的偏离程度”衡量好坏，而不是原始值；
复杂场景下，“只有某段区间有信号” 之前，一般都会先 winsorize+zscore 做“干净版本”。
normalize(A, useStd=false)

场景：
想让 alpha 向量满足一些约束（如和为 0、绝对和为 1 等）以方便回测；
已经认定好坏排序无误，只需要变成实际可交易权重。
quantile(A, driver=gaussian|cauchy|uniform)

场景：
只信 rank，不信原始间距；
想把头尾拉长、中间压缩，使“头尾区域贡献更大，中间区间噪音影响更小”；
比如：quantile(A,"gaussian") 把中间堆在 0 附近，两头往远处拉。
truncate(A, maxPercent=0.01)

场景：
想严格限制任一股票最大权重，即便因子极端也不能超出；
如“即便最好的 ESG 也最多只占 1% booksize”，挤出一部分极端风险。
scale(A, scale=1, longscale=1, shortscale=1)

场景：
控制多空强度，比如多头总权重=1，空头总权重=-1；
或者想让“好公司”仓位更集中、坏公司更分散：用不同的 longscale/shortscale。
四、分组运算符（group_rank / group_zscore / group_scale / group_normalize / group_mean / group_backfill / group_cartesian_product）

group_rank(A, group)

场景：
你觉得“信号只在组内排序上有意义”，不同组之间原始水平不能比；
如 ESG 按行业比，行业间 ESG 水平不具可比性。
group_zscore(A, group)

场景：
你想在行业内做“高于行业平均几个标准差”的度量；
尤其当某些行业整体 ESG 水平很高/很低时，需要去掉这一层偏移。
group_scale(A, group)

场景：
想要每个行业内的 A 从 0～1 线性分布，方便配合逻辑/桶化；
比如只做“行业内 Top 20%”选股，之前先 group_scale 再用阈值。
group_normalize(A, group)

场景：
想做到每天每个行业“净多空为 0 / 杠杆受控”，避免行业间暴露；
单因子 A 决定组内排序，同时这个运算符决定组内权重如何平衡。
group_backfill(A, group, d)

场景：
某个行业里个别股票 ESG 缺数据，你想用同组历史均值/邻近值填充，用于维持样本量；
防止某些组因缺值导致权重集中在少数有数据的成员。
group_cartesian_product(g1, g2)

场景：
想在“行业 × 国家”“行业 × size”等更细粒度 group 内排序；
对于只在特定子群（如小盘高 ESG）才有信号的因子特别有用。
五、变换/筛选类（bucket / right_tail / left_tail / trade_when）

bucket(rank(A), range="0,1,0.1")

场景：
你相信“只有前 10%/后 10% 的 A 有信号，中间是噪音”，想做分组处理；
分桶后可以对不同桶施加不同逻辑（比如头部多、尾部空、中间 0）。
right_tail(A, minimum)

场景：
想把“低于某值”的都视为噪音（NaN），只在右尾上做信号；
例如只关心 ESG 行业分位>70%的公司，中低段看成无信号。
left_tail(A, maximum)

场景：
想把“高于某值”的都视为噪音，只在左尾（差公司）上建反向信号；
如“只做最低 ESG 10% 的反向因子”，其余不参与。
trade_when(A, ...)

场景：
将“某区间内”的值替换为 0 / NaN / 别的逻辑输出，从而只在有信号区间交易；
用于构造“区间择时”：例如仅当 A 超过某阈值时，才重新调整权重。
六、时间序列运算符（ts_mean / ts_rank / ts_delta / ts_zscore / ts_scale / ts_sum / ts_std_dev / ts_decay_linear / hump / hump_decay / ts_target_tvr_ / ts_backfill / ts_median / ts_quantile / ts_arg_max / ts_arg_min / ts_corr / ts_covariance / last_diff_value / days_from_last_change / ts_product / ts_step / ts_count_nans / ts_regression / kth_element / inst_tvr）*

这些主要用于“时序上更好才是更好”的场景。

ts_mean(A, d) / ts_median(A,d)

场景：
你认为“持续高 ESG / 高盈利”的公司更可靠，而不是只看某一时点；
则用近 d 天平均/中位数来平滑一次性噪音。
ts_delta(A, d)

场景：
“变好”比“绝对高”更重要，例如 ESG 评分持续上升；
A_t - A_{t-d} > 0 代表在改善，可用作单独因子或与水平因子叠加。
ts_rank(A, d) / ts_zscore(A,d) / ts_scale(A,d)

场景：
你关心 A 在自身过去窗口中的位置，“历史高位/低位”是否预示未来表现；
如 ESG 刚刷新历史高值是否会带来短期 alpha。
ts_decay_linear(A, d) / ts_decay_exp_window(A,d)

场景：
A 每天抖动大，但方向稳定，希望平滑，用“加权平均最近几天”的方式；
控制周频/日频噪音，不改变整体趋势。
hump(A, hump=0.01) / hump_decay(A, ...)

场景：
控制日间权重变化幅度，忽略太小的变化，降低 turnover；
当你知道因子信号慢变，不需要对小抖动频繁调仓时。
ts_target_tvr_* 一族

场景：
有明确 turnover 目标，想自动调整 decay 相关参数；
对于已经验证有信号但过于频繁交易的因子，做“统一降速”。
ts_backfill(A, lookback, ...) / kth_element

场景：
在时间维度上填补缺失 A，减少由于少数缺值导致的随机信号。
days_from_last_change(A) / last_diff_value(A,d)

场景：
因子是“事件驱动型”的（评级变动、ESG 评级更新等），只在变动后若干天内才有信号；
可以构造“距上次变化时间”的信号。
七、Vector Operator*
这些用于处理“向量类型数据”，需要先生成统计特征才能用。

补充：常用 Vector Operators（Combo, Regular）

> 一句话描述：Vector 字段（例如一只股票一天里的一串向量值）不能直接参与普通的算术/时序/截面运算，通常需要先用 `vec_*` 把它“降维”为标量特征（均值/分位/波动/偏度等），再进入后续流程。

- `vec_avg(x)`（base）：对向量求均值。例：输入 (2,3,5,6,3,8,10) 输出 37/7=5.29
- `vec_sum(x)`（base）：对向量求和。例：输入 (2,3,5,6,3,8,10) 输出 37
- `vec_count(x)`（genius）：向量元素个数
- `vec_choose(x, nth=k)`（genius）：取向量中第 k 个元素（从 0 开始计数）
- `vec_max(x)`（genius）：向量最大值
- `vec_min(x)`（genius）：向量最小值
- `vec_range(x)`（genius）：向量极差（max-min）
- `vec_stddev(x)`（genius）：向量标准差
- `vec_ir(x)`（genius）：向量信息比率（均值/标准差）
- `vec_skewness(x)`（genius）：向量偏度
- `vec_kurtosis(x)`（genius）：向量峰度
- `vec_norm(x)`（genius）：向量范数（所有元素绝对值之和）
- `vec_percentage(x, percentage=0.5)`（genius）：向量分位数（如 0.5 为中位数）
- `vec_powersum(x, constant=2)`（genius）：向量幂和（对每个元素做幂后求和）
- `vec_filter(vec, value=nan)`（genius）：按值过滤向量（可一次过滤多个值，例如 `"nan 0 10"`）。注意：输出仍然是 VECTOR 类型（还未降维）。

注意：
- Vector type 数据不能直接用；你必须先用一个 `vec_*` 把它变成标量特征后再做后续组合。
- `vec_*` 只能作用在 VECTOR 类型数据上；普通 MATRIX 字段不能直接喂给 `vec_*`。



小结：
只头部/尾部有信号：
想起：rank + bucket + 逻辑运算符（greater/less/if_else/trade_when）、right_tail / left_tail。
中间区间是噪音：
想起：用阈值+逻辑把中段置 0 / NaN（if_else/trade_when），或 quantile 把中间压在 0 附近。
极值是噪音：
想起：winsorize、truncate、log/s_log_1p 以及 group 版处理。
时序上持续更好才是“好”：
想起：ts_mean / ts_median / ts_rank / ts_delta / ts_zscore / ts_decay_linear 与 hump。
只在某些 group 中有用信号（行业/国家/size）：
想起：group_rank / group_zscore / group_scale / group_normalize / group_cartesian_product。
如果你愿意，下一步我可以挑一个具体字段（比如 anl11_esgreg_industryperc），分别用“头尾信号型 / 极值噪音型 / 时序改善型 / group 内相对型”4 种典型场景，各写一个短而实战的 Alpha 表达式，让你一眼看到这些运算符在真实情境下的用法差别。


---------------------------------------------------------------------------------------------
先说思路，再按运算符类别给“B 的安全用法模板”。

目标回顾

已有主信号 A（决定方向和主排序）。
从属信号 B 只能：
放大/缩小 A 的力度；
或在“已确定阵营”的前提下微调排序；
不能：翻转方向、让 B 在全局上主导排序。
下面假设 A 已经是你认可的版本（例如 A = zscore(winsorize(returns,4))），我们只讨论 “在 A 基础上怎样用 B”。

一、Arithmetic 类运算符（add / subtract / multiply / reverse / power / signed_power / log / sqrt / s_log_1p / abs / inverse / max / min）

这里关键：让 B 进入一个受控区间，再影响 A。

add(B,c) / subtract(B,c)

用途：给 B 平移到围绕 0 的小区间。
模板：
b = zscore(winsorize(B,4))
b_clip = winsorize(b, 2)
再进入其他结构（见 multiply）。
multiply(A, something(B))

安全范式：
factor = 1 + k * b_clip，其中 b_clip 已限制在[-1,1]，k 小于 1；
core = A * factor
示例：
b = zscore(winsorize(B,4))
b_clip = winsorize(b,2)
factor = add(1, multiply(0.5, b_clip)) （≈ 0.5~1.5）
core = multiply(A, factor, filter=true)
这样：
sign(core) = sign(A)；
|core| 随 B 增大/减小。
reverse(B) / inverse(B)（1/B）

只适合作为 构造 factor 的中间步骤，仍要映射到有限区间：
如：b_inv = inverse(B) → 再 zscore + winsorize + 映射到 [0.5,1.5]；
不要 A * inverse(B) 直接上，会把稀奇小值放大得乱七八糟。
power(B,y) / signed_power(B,y)

用途：
y>1：强调高 B；0<y<1：压平 B。
模式：
b = zscore(B) → b_clip = winsorize(b,2) → b2 = signed_power(b_clip, y) → 再缩放成 factor。
依然走 “factor = 1 + k*b2” 的套路。
log(B) / sqrt(B)

用途：B>0 且右偏时压尾，避免少数巨大成交量/市值主导因子。
一般流程：b = log(B) 或 sqrt(B) → 标准化、截断 → 做 factor。
s_log_1p(B)

用途：既压缩幅度又保留正负号，适合已 zscore 的 B：
b = zscore(winsorize(B,4)) → b2 = s_log_1p(b)；b2 自动收在有限范围。
abs(B) / max(A,B) / min(A,B)

用途：
abs(B)：我们只关心“B 极端程度”而非方向，例如极大成交量时更值得放大；
可用：factor = 1 + k * s_log_1p(abs(zscore(B)))。
max/min 不用于 A×B，而常用来在两种 factor 中选更强/更弱的一个。
二、Logical 类（and / or / not / greater / less / equal / not_equal / if_else / is_nan）

这里 B 更像“开关/权重档位”。

区间筛选：只在某些 B 区间放大或允许交易

例：B 为 volume，成交量太小的股票不想重仓：
high_liq = greater(B, thresh)
core = if_else(high_liq, A, 0.5*A) 或 trade_when(not high_liq, 0.5*A, A)。
模式：
B 只决定“用 A 还是 c*A”，而不是参与算术组合。
多条件：B 只是辅助条件，不决定符号

如：收益为正，且成交量高时才加大多头：
long = greater(A,0)
high_vol = greater(B, thresh)
boost = and(long, high_vol)
core = trade_when(boost, 1.5*A, A)。
is_nan(B)

用 B 的缺失与否控制是否用其影响：
has_B = not(is_nan(B))
core = trade_when(has_B, A * factor(B), A)。
三、Cross-sectional 形状控制（winsorize / zscore / normalize / quantile / rank / truncate / scale）

这些几乎是所有 “B 处理” 的第一步。

对 B 做“干净版处理”：

标准套路：
b = zscore(winsorize(B,4))
或 b_rank = rank(B)
或 b_q = quantile(B,"gaussian")。
关键：B 必须先被裁剪和标准化，再参与任何与 A 的组合。
用 rank(B) 时特别注意：

若你直接 A * rank(B)，B 会在[0,1]里直接线性放大/缩小 A（可接受）；
真正危险的是 rank(A) * rank(B) 类型，“双 rank 全局扭曲排序”；
安全模式：
core = A * f(rank(B))，且 f 在有限区间（比如 [0.5,1.5]）。
quantile(B, driver)

适合把 B 的中间区间压到 0 附近，让“只有极高/极低的 B 才明显放大/抑制 A”；
再映射到小系数范围即可。
truncate / scale

truncate(A, x)：作用于合成后的 core，保证任何单股票权重不爆；
scale：多空总和、booksize 控制，与 B 关系不大，但最后一步常用。
四、Group 类（group_rank / group_zscore / group_scale / group_normalize / group_backfill / group_mean）

当 B 的含义“只在 group 内比较有意义”（如行业内量能/市值）：

Group 内标准化 B：

b = group_zscore(B, industry) 或 b_rank = group_rank(B, industry)；
然后用作 factor 的原材料。
典型安全模式：

factor = 1 + k * group_zscore(B, industry) 截断在[-1,1]；
或在多头/空头阵营内用 group_rank(B, group) 调整权重。
不要用 group 结果去改变 A 的方向，只影响幅度和组内排序。

五、Transformational（bucket / right_tail / left_tail / trade_when / right_tail/left_tail 已讲）

bucket(rank(B), ...)

场景：把 B 分为“极高 / 高 / 中 / 低 / 极低”，然后每个桶给不同放大倍数：
模式：
b_rank = rank(B)
b_bucket = bucket(b_rank, "0,1,0.2")
再 if_else / trade_when：
极高桶：乘 1.5；高桶：乘 1.2；中桶：乘 1；低桶：乘 0.7；极低桶：乘 0.5。
注意：始终是 “A * f(bucket(B))”。
right_tail / left_tail

提前把“无意义区间”的 B 变 NaN，然后只在 B 有意义区间里做放大；
如：b_sig = right_tail(zscore(B), minimum=0) → 只对高量能时放大 A，其余 factor=1。
trade_when（上面已部分提过）

是最通用的 “条件改变 A 倍数或关闭仓位” 工具。
样板：
cond = some_function_of_B
core = trade_when(cond, A * factor1, A * factor2)。
六、Time Series 类（ts_mean / ts_rank / ts_delta / ts_zscore / ts_decay_linear / hump 等）

这里 B 是时序信号，比如 volume, adv, 波动率等。

基础清洗：

b_ts = ts_zscore(B, d) 或 ts_rank(B,d)；
用于识别“这个股票近期 volume 特别高/特别低”。
安全组合范式：

factor = 1 + k * ts_zscore(B,d) 截断；
或 factor = f(ts_rank(B,d)) 映射到 [0.5,1.5]；
再 core = A * factor。
Turnover 控制相关（ts_decay_linear / hump / ts_target_tvr_*）：

这些更多用于平滑最终 Alpha，而不是直接处理 B；
可在合成 core 后：core_smooth = ts_decay_linear(core, 3)；B 的作用已经体现在 core 里。
ts_delta(B,d) / days_from_last_change(B)

把“最近量能/波动突变”作为从属放大器；
例如 volume 爆量那几天放大 A，平时保持中立：
b_spike = greater(ts_delta(B,1), thresh)
core = trade_when(b_spike, 1.5*A, A)。


最后给一个总的“使用从属 B 的模板公式”

可以抽象成：

先得到干净的主信号：

A_clean = some_transform_on_A(...)（你已完成）
再把 B 变成有限、解释清晰的放大器：

结构 1：线性缩放

B_clean = standardize_and_clip(B)
factor = 1 + k * B_clean （k 小于 1，B_clean 在[-1,1]）
core = A_clean * factor
结构 2：按阵营分配

基于 A 确定阵营：long_mask = A_clean>0，short_mask = A_clean<0
在每个阵营内部，用 rank(B) / group_rank(B,industry) 再调节：
factor_long = f(rank(B | long_mask))
factor_short = g(rank(B | short_mask))
core = trade_when(long_mask, A_clean*factor_long, A_clean) 再对空头同理。
最后再 normalize / scale / truncate 做可交易化。
只要你保证“B 只出现在 factor 里，且 factor 不会跨 0”，主信号 A 的方向和骨干排序就不会被 B 颠覆。

### Smoothing Operators
- **ts_mean vs ts_decay_linear**:
    - `ts_mean(x, N)` puts equal weight on all N days.
    - `ts_decay_linear(x, N)` puts linearly decreasing weight (N, N-1, ..., 1).
    - **Turnover Impact**: `ts_decay_linear` results in **much higher turnover** than `ts_mean` for the same window size, because it emphasizes recent data.
    - Example: `ts_mean(x, 20)` -> Turnover 16%. `ts_decay_linear(x, 20)` -> Turnover 73%.
    - **Recommendation**: Use `ts_mean` for reducing turnover. Use `ts_decay_linear` only if you need faster reaction and can afford the turnover.