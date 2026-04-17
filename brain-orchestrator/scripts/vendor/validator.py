#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表达式验证器 - 使用抽象语法树验证字符串表达式格式是否正确

本模块实现了一个能够检测字符串表达式格式是否正确的系统，基于PLY(Python Lex-Yacc)
构建词法分析器和语法分析器，识别表达式中的操作符、函数和字段，并验证其格式正确性。
"""

import re
import sys
import json
import os
from typing import List, Dict, Any, Optional, Tuple

# Optional whitelist of allowed operators loaded from validOp.json.
_ALLOWED_OPERATOR_NAMES: Optional[set] = None


def _resolve_valid_op_json_path() -> Optional[str]:
    env_path = os.getenv('BRAIN_VALID_OP_PATH')
    if env_path and os.path.isfile(env_path):
        return env_path

    base = os.path.abspath(os.path.dirname(__file__))
    for _ in range(10):
        candidates = [
            os.path.join(base, 'validOp.json'),
            os.path.join(base, 'APP', 'validOp.json'),
            os.path.join(base, 'untracked', 'APP', 'validOp.json'),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        parent = os.path.dirname(base)
        if parent == base:
            break
        base = parent

    return None


def _get_allowed_operator_names() -> Optional[set]:
    global _ALLOWED_OPERATOR_NAMES
    if _ALLOWED_OPERATOR_NAMES is not None:
        return _ALLOWED_OPERATOR_NAMES

    path = _resolve_valid_op_json_path()
    if not path:
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return None

    names = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'name' in item:
                names.add(str(item['name']).lower())

    _ALLOWED_OPERATOR_NAMES = names
    return _ALLOWED_OPERATOR_NAMES

# 尝试导入PLY库，如果不存在则提供安装提示
try:
    import ply.lex as lex
    import ply.yacc as yacc
except ImportError:
    print("错误: 需要安装PLY库。请运行 'pip install ply' 来安装。")
    sys.exit(1)

# 1. 定义支持的操作符和函数
supported_functions = {
    # Group 类别函数
    'group_min': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    # group_mean(x, w, group)
    'group_mean': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'category']},
    'group_median': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_max': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_rank': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_vector_proj': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'category']},
    'group_normalize': {'min_args': 2, 'max_args': 5, 'arg_types': ['expression', 'category', 'expression', 'expression', 'expression']},
    'group_extra': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'category']},
    'group_backfill': {'min_args': 3, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'expression'], 'param_names': ['x', 'cat', 'days', 'std']},
    'group_scale': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_count': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_zscore': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_std_dev': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_sum': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_neutralize': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'category']},
    'group_multi_regression': {'min_args': 4, 'max_args': 9, 'arg_types': ['expression'] * 9},
    'group_cartesian_product': {'min_args': 2, 'max_args': 2, 'arg_types': ['category', 'category']},
    'combo_a': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression']},
    
    # Transformational 类别函数
    'right_tail': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'bucket': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # 第二个参数可以是string类型的range参数
    'tail': {'min_args': 1, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'expression']},
    'left_tail': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'trade_when': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression']},
    'generate_stats': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    
    # Cross Sectional 类别函数
    'winsorize': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'number', 'boolean'], 'param_names': ['x', 'std', 'clip'], 'keyword_only_from': 1},
    'rank': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'regression_proj': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'vector_neut': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'regression_neut': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'multi_regression': {'min_args': 2, 'max_args': 100, 'arg_types': ['expression'] * 100},  # 支持多个自变量
    
    # Time Series 类别函数
    'ts_std_dev': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_mean': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_delay': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_corr': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number']},
    'ts_zscore': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_returns': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'mode'], 'keyword_only': True},
    'ts_product': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    # Platform: ts_backfill(x, d)
    'ts_backfill': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'd']},
    'days_from_last_change': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'last_diff_value': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    # Platform: ts_scale(x, d, constant=0)
    'ts_scale': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'constant'], 'keyword_only': True},
    # Platform: ts_entropy(x, d)
    'ts_entropy': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'd']},
    'ts_step': {'min_args': 1, 'max_args': 1, 'arg_types': ['number']},
    'ts_sum': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_co_kurtosis': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number']},
    'inst_tvr': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_decay_exp_window': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'factor'], 'keyword_only': True},
    'ts_av_diff': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_kurtosis': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    # Platform: ts_min_max_diff(x, d, f=0.5)
    'ts_min_max_diff': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'f'], 'keyword_only': True},
    'ts_arg_max': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_max': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    # Platform: ts_min_max_cps(x, d, f=2)
    'ts_min_max_cps': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'f'], 'keyword_only': True},
    # Platform: ts_rank(x, d, constant=0)
    'ts_rank': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'constant'], 'keyword_only': True},
    'ts_ir': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_theilsen': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number']},
    # Platform: hump_decay(x, p=0)
    'hump_decay': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'p'], 'keyword_only': True},
    # Platform: ts_weighted_decay(x, k=0.5)
    'ts_weighted_decay': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'k'], 'keyword_only': True},
    # Platform: ts_quantile(x, d, driver="gaussian")
    'ts_quantile': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'string'], 'param_names': ['x', 'd', 'driver'], 'keyword_only': True},
    'ts_min': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_count_nans': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_covariance': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number']},
    'ts_co_skewness': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number']},
    'ts_min_diff': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    # Platform: ts_decay_linear(x, d, dense=false)
    'ts_decay_linear': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'boolean'], 'param_names': ['x', 'd', 'dense'], 'keyword_only': True},
    # Platform: jump_decay(x, d, sensitivity=0.5, force=0.1)
    'jump_decay': {'min_args': 2, 'max_args': 4, 'arg_types': ['expression', 'number', 'number', 'number'], 'param_names': ['x', 'd', 'sensitivity', 'force'], 'keyword_only': True},
    # Platform: ts_moment(x, d, k=0)
    'ts_moment': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'k'], 'keyword_only': True},
    'ts_arg_min': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_regression': {'min_args': 3, 'max_args': 5, 'arg_types': ['expression', 'expression', 'number', 'number', 'number'], 'param_names': ['y', 'x', 'd', 'lag', 'rettype'], 'keyword_only': True},
    'ts_skewness': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_max_diff': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'kth_element': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'number', 'number']},
    'hump': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'hump']},
    'ts_median': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_delta': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    # Platform: ts_poly_regression(y, x, d, k=1) and k must be keyword if provided
    'ts_poly_regression': {'min_args': 3, 'max_args': 4, 'arg_types': ['expression', 'expression', 'number', 'number'], 'param_names': ['y', 'x', 'd', 'k'], 'keyword_only': True, 'keyword_only_from': 3},
    'ts_target_tvr_decay': {'min_args': 1, 'max_args': 4, 'arg_types': ['expression', 'number', 'number', 'number'], 'param_names': ['x', 'lambda_min', 'lambda_max', 'target_tvr'], 'keyword_only': True},
    'ts_target_tvr_delta_limit': {'min_args': 2, 'max_args': 5, 'arg_types': ['expression', 'expression', 'number', 'number', 'number'], 'param_names': ['x', 'y', 'lambda_min', 'lambda_max', 'target_tvr'], 'keyword_only': True},
    'ts_target_tvr_hump': {'min_args': 1, 'max_args': 4, 'arg_types': ['expression', 'number', 'number', 'number'], 'param_names': ['x', 'lambda_min', 'lambda_max', 'target_tvr'], 'keyword_only': True},
    # Platform: ts_delta_limit(x, y, limit_volume=0.1)
    'ts_delta_limit': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number'], 'param_names': ['x', 'y', 'limit_volume'], 'keyword_only': True},
    
    # Special 类别函数
    'inst_pnl': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'self_corr': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'in': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # 注意：这是关键字
    'universe_size': {'min_args': 0, 'max_args': 0, 'arg_types': []},
    
    # Missing functions from operators.py
    'quantile': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['x', 'driver', 'sigma']},  # quantile(x, driver = gaussian, sigma = 1.0)
    'normalize': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'boolean', 'number']},  # normalize(x, useStd = false, limit = 0.0)
    'zscore': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},  # zscore(x)
    
    # Logical 类别函数
    'or': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # 注意：这是关键字
    'and': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # 注意：这是关键字
    'not': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},  # 注意：这是关键字
    'is_nan': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'is_not_nan': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'less': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'equal': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'greater': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'is_finite': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'if_else': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression']},
    'not_equal': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'less_equal': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'greater_equal': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    
    # Vector 类别函数
    'vec_kurtosis': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_min': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_count': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_sum': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_skewness': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_max': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_avg': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_range': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_choose': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'nth']},
    'vec_powersum': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'constant']},
    'vec_stddev': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_percentage': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'percentage']},
    'vec_ir': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'vec_norm': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'ts_percentage': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'd', 'percentage'], 'keyword_only': True},
    'signed_power': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    'ts_product': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number']},
    
    # Additional functions from test cases
    'rank_by_side': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'number', 'number'], 'param_names': ['x', 'rate', 'scale']},
    'log_diff': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'nan_mask': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},
    'ts_partial_corr': {'min_args': 4, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'number']},
    'ts_triple_corr': {'min_args': 4, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'number']},
    'clamp': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['x', 'lower', 'upper']},
    'keep': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number'], 'param_names': ['x', 'condition', 'period']},
    'replace': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['x', 'target', 'dest']},
    'filter': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['x', 'h', 't']},
    'one_side': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'string'], 'param_names': ['x', 'side']},
    'scale_down': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'number'], 'param_names': ['x', 'constant']},
    
    # Arithmetic 类别函数
    # add(x, y, ..., filter=false)
    # NOTE: add() is variadic (>=2 terms) with an optional boolean filter flag.
    # We validate it with custom logic in validate_function().
    'add': {'min_args': 2, 'max_args': 101, 'arg_types': ['expression'] * 101},
    'multiply': {'min_args': 2, 'max_args': 100, 'arg_types': ['expression'] * 99 + ['boolean'], 'param_names': ['x', 'y', 'filter']},  # multiply(x, y, ..., filter=false)
    'sign': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'subtract': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'expression', 'boolean']},  # subtract(x, y, filter=false)
    'pasteurize': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'log': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'purify': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'arc_tan': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'max': {'min_args': 2, 'max_args': 100, 'arg_types': ['expression'] * 100},  # max(x, y, ...)
    'to_nan': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'expression', 'boolean']},  # to_nan(x, value=0, reverse=false)
    'abs': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'sigmoid': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'divide': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # divide(x, y)
    'min': {'min_args': 2, 'max_args': 100, 'arg_types': ['expression'] * 100},  # min(x, y, ...)
    'tanh': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'nan_out': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['x', 'lower', 'upper']},  # nan_out(x, lower=0, upper=0)
    'signed_power': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # signed_power(x, y)
    'inverse': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'round': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'sqrt': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    's_log_1p': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'reverse': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},  # -x
    'power': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression']},  # power(x, y)
    'densify': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    'floor': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression']},
    # Appended missing operators
    'arc_cos': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['x']},
    'arc_sin': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['x']},
    'ceiling': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['x']},
    'exp': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['x']},
    'fraction': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['x']},
    'round_down': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['x', 'f']},
    'is_not_finite': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'negate': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'ts_rank_gmean_amean_diff': {'min_args': 5, 'max_args': 5, 'arg_types': ['expression', 'expression', 'expression', 'expression', 'number'], 'param_names': ['input1', 'input2', 'input3', '...', 'd']},
    'ts_vector_neut': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number'], 'param_names': ['x', 'y', 'd']},
    'ts_vector_proj': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'number'], 'param_names': ['x', 'y', 'd']},
    'scale': {'min_args': 1, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'expression'], 'param_names': ['x', 'scale', 'longscale', 'shortscale']},
    'generalized_rank': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['open', 'm']},
    'rank_gmean_amean_diff': {'min_args': 4, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'expression'], 'param_names': ['input1', 'input2', 'input3', '...']},
    'truncate': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['x', 'maxPercent']},
    'vector_proj': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['x', 'y']},
    'vec_filter': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['vec', 'value']},
    'group_coalesce': {'min_args': 4, 'max_args': 4, 'arg_types': ['expression', 'expression', 'expression', 'expression'], 'param_names': ['original_group', 'group2', 'group3', '…']},
    'group_percentage': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'category', 'expression'], 'param_names': ['x', 'group', 'percentage']},
    'group_vector_neut': {'min_args': 3, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['x', 'y', 'g']},
    'convert': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['x', 'mode']},
    'reduce_avg': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['input', 'threshold']},
    'reduce_choose': {'min_args': 2, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['input', 'nth', 'ignoreNan']},
    'reduce_count': {'min_args': 2, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['input', 'threshold']},
    'reduce_ir': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_kurtosis': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_max': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_min': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_norm': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_percentage': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['input', 'percentage']},
    'reduce_powersum': {'min_args': 1, 'max_args': 3, 'arg_types': ['expression', 'expression', 'expression'], 'param_names': ['input', 'constant', 'precise']},
    'reduce_range': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_skewness': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
    'reduce_stddev': {'min_args': 1, 'max_args': 2, 'arg_types': ['expression', 'expression'], 'param_names': ['input', 'threshold']},
    'reduce_sum': {'min_args': 1, 'max_args': 1, 'arg_types': ['expression'], 'param_names': ['input']},
}

# 2. 定义group类型字段
group_fields = {
    'sector', 'subindustry', 'industry', 'exchange', 'country', 'market'
}

# 3. 有效类别集合
valid_categories = group_fields

# 4. 字段命名模式 - 只校验字段是不是数字字母下划线组成
field_patterns = [
    re.compile(r'^[a-zA-Z0-9_]+$'),  # 只允许数字、字母和下划线组成的字段名
]

# 4. 抽象语法树节点类型
class ASTNode:
    """抽象语法树节点基类"""
    def __init__(self, node_type: str, children: Optional[List['ASTNode']] = None, 
                 value: Optional[Any] = None, line: Optional[int] = None):
        self.node_type = node_type  # 'function', 'operator', 'field', 'number', 'expression'
        self.children = children or []
        self.value = value
        self.line = line
    
    def __str__(self) -> str:
        return f"ASTNode({self.node_type}, {self.value}, line={self.line})"
    
    def __repr__(self) -> str:
        return self.__str__()

class ExpressionValidator:
    """表达式验证器类"""
    
    def __init__(self):
        """初始化词法分析器和语法分析器"""
        # 构建词法分析器
        self.lexer = lex.lex(module=self, debug=False)
        # 构建语法分析器
        self.parser = yacc.yacc(module=self, debug=False)
        # 错误信息存储
        self.errors = []
        # Cache for unit inference (unit/scalar/category)
        self._unit_cache: Dict[int, str] = {}
        # Cache for derived category detection (bucket/group_cartesian_product outputs)
        self._derived_category_cache: Dict[int, bool] = {}
    
    # 词法分析器规则
    tokens = ('FUNCTION', 'FIELD', 'NUMBER', 'LPAREN', 'RPAREN', 
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'COMMA', 'CATEGORY',
              'EQUAL', 'ASSIGN', 'IDENTIFIER', 'STRING', 'GREATER', 'LESS', 'GREATEREQUAL', 'LESSEQUAL', 'NOTEQUAL', 'BOOLEAN')
    
    # 忽略空白字符
    t_ignore = ' \t\n'
    
    # 操作符 - 注意顺序很重要，长的操作符要放在前面
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','    
    t_EQUAL = r'=='
    t_NOTEQUAL = r'!='
    t_GREATEREQUAL = r'>='
    t_LESSEQUAL = r'<='
    t_GREATER = r'>'
    t_LESS = r'<'
    t_ASSIGN = r'='
    
    # 数字（整数和浮点数）
    def t_NUMBER(self, t):
        r'\d+\.?\d*'
        if '.' in t.value:
            t.value = float(t.value)
        else:
            t.value = int(t.value)
        return t
    
    # 字符串 - 需要放在所有其他标识符规则之前
    def t_STRING(self, t):
        r"'[^']*'|\"[^\"]*\""
        # 去除引号
        t.value = t.value[1:-1]
        return t
    
    # 函数和字段名
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        # 检查是否为布尔值
        if t.value.lower() in {'true', 'false'}:
            t.type = 'BOOLEAN'
            t.value = t.value.lower()  # 转换为小写以保持一致性
        else:
            # 查看当前token后面的字符，判断是否为参数名（后面跟着'='）
            lexpos = t.lexpos
            next_chars = ''
            if lexpos + len(t.value) < len(t.lexer.lexdata):
                # 查看当前token后面的字符，跳过空格
                next_pos = lexpos + len(t.value)
                while next_pos < len(t.lexer.lexdata) and t.lexer.lexdata[next_pos].isspace():
                    next_pos += 1
                if next_pos < len(t.lexer.lexdata):
                    next_chars = t.lexer.lexdata[next_pos:next_pos+1]
            
            # 如果后面跟着'='，则为参数名
            if next_chars == '=':
                t.type = 'IDENTIFIER'
            # 如果后面跟着'('，则为函数名
            elif next_chars == '(':
                t.type = 'FUNCTION'
                t.value = t.value.lower()  # 转换为小写以保持一致性
            # 检查是否为参数名（支持更多参数名）
            elif t.value in {'std', 'k', 'lambda_min', 'lambda_max', 'target_tvr', 'range', 'buckets', 'lag', 'rettype', 'mode', 'nth', 'constant', 'percentage', 'driver', 'sigma', 'rate', 'scale', 'filter', 'lower', 'upper', 'target', 'dest', 'event', 'sensitivity', 'force', 'h', 't', 'period', 'stddev', 'factor', 'k', 'useStd', 'limit', 'gaussian', 'uniform', 'cauchy'}:
                t.type = 'IDENTIFIER'
            # 检查是否为函数名（不区分大小写）
            elif t.value.lower() in supported_functions:
                t.type = 'FUNCTION'
                t.value = t.value.lower()  # 转换为小写以保持一致性
            # 检查是否为有效类别
            elif t.value in valid_categories:
                t.type = 'CATEGORY'
            # 检查是否为字段名
            elif self._is_valid_field(t.value):
                t.type = 'FIELD'
            else:
                # 其他标识符，保留为IDENTIFIER类型
                t.type = 'IDENTIFIER'
        return t
    
    # 行号跟踪
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
    
    # 错误处理
    def t_error(self, t):
        if t:
            # 检查是否为非法字符
            if not re.match(r'[a-zA-Z0-9_\+\-\*/\(\)\,\s=<>!]', t.value[0]):
                # 这是一个非法字符
                self.errors.append(f"非法字符 '{t.value[0]}' (行 {t.lexer.lineno})")
            else:
                # 这是一个非法标记
                self.errors.append(f"非法标记 '{t.value}' (行 {t.lexer.lineno})")
            # 跳过这个字符，继续处理
            t.lexer.skip(1)
        else:
            self.errors.append("词法分析器到达文件末尾")
    
    # 语法分析器规则
    def p_expression(self, p):
        """expression : comparison
                      | expression EQUAL comparison
                      | expression NOTEQUAL comparison
                      | expression GREATER comparison
                      | expression LESS comparison
                      | expression GREATEREQUAL comparison
                      | expression LESSEQUAL comparison"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ASTNode('binop', [p[1], p[3]], {'op': p[2]})
    
    def p_comparison(self, p):
        """comparison : term
                      | comparison PLUS term
                      | comparison MINUS term"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ASTNode('binop', [p[1], p[3]], {'op': p[2]})
    
    def p_term(self, p):
        """term : factor
                | term TIMES factor
                | term DIVIDE factor"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ASTNode('binop', [p[1], p[3]], {'op': p[2]})
    
    def p_factor(self, p):
        """factor : NUMBER
                  | STRING
                  | FIELD
                  | CATEGORY
                  | IDENTIFIER
                  | BOOLEAN
                  | MINUS factor
                  | LPAREN expression RPAREN
                  | function_call"""
        if len(p) == 2:
            # 数字、字符串、字段、类别或标识符
            if p.slice[1].type == 'NUMBER':
                p[0] = ASTNode('number', value=p[1])
            elif p.slice[1].type == 'STRING':
                p[0] = ASTNode('string', value=p[1])
            elif p.slice[1].type == 'FIELD':
                p[0] = ASTNode('field', value=p[1])
            elif p.slice[1].type == 'CATEGORY':
                p[0] = ASTNode('category', value=p[1])
            elif p.slice[1].type == 'BOOLEAN':
                p[0] = ASTNode('boolean', value=p[1])
            elif p.slice[1].type == 'IDENTIFIER':
                p[0] = ASTNode('identifier', value=p[1])
            else:
                p[0] = p[1]
        elif len(p) == 3:
            # 一元负号
            p[0] = ASTNode('unop', [p[2]], {'op': p[1]})
        elif len(p) == 4:
            # 括号表达式
            p[0] = p[2]
        else:
            # 函数调用
            p[0] = p[1]
    
    def p_function_call(self, p):
        '''function_call : FUNCTION LPAREN args RPAREN'''
        p[0] = ASTNode('function', p[3], p[1])
    
    def p_args(self, p):
        '''args : arg_list
                | empty'''
        if len(p) == 2 and p[1] is not None:
            p[0] = p[1]
        else:
            p[0] = []
    
    def p_arg_list(self, p):
        '''arg_list : arg
                   | arg_list COMMA arg'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]
    
    def p_arg(self, p):
        '''arg : expression
              | IDENTIFIER ASSIGN expression'''
        if len(p) == 2:
            p[0] = {'type': 'positional', 'value': p[1]}
        else:
            p[0] = {'type': 'named', 'name': p[1], 'value': p[3]}
    
    def p_empty(self, p):
        '''empty :'''
        p[0] = None
    
    # 语法错误处理
    def p_error(self, p):
        if p:
            self.errors.append(f"语法错误在位置 {p.lexpos}: 非法标记 '{p.value}'")
        else:
            self.errors.append("语法错误: 表达式不完整")
    
    def _is_valid_field(self, field_name: str) -> bool:
        """检查字段名是否符合模式"""
        for pattern in field_patterns:
            if pattern.match(field_name):
                return True
        return False
    
    def validate_function(self, node: ASTNode, is_in_group_arg: bool = False) -> List[str]:
        """验证函数调用的参数数量和类型"""
        function_name = node.value
        args = node.children

        allowed_ops = _get_allowed_operator_names()
        if allowed_ops is not None and function_name not in allowed_ops:
            return [f"不允许的运算符: {function_name}"]

        function_info = supported_functions.get(function_name)
        
        if not function_info:
            return [f"未知函数: {function_name}"]
        
        # Custom validation for variadic functions with optional flags
        if function_name == 'add':
            return self._validate_add(args, is_in_group_arg)
        if function_name == 'winsorize':
            return self._validate_winsorize(args, is_in_group_arg)

        errors = []

        # Keyword-only enforcement for optional parameters.
        # If enabled, only the required leading arguments can be positional.
        keyword_only_from = function_info.get('keyword_only_from')
        if keyword_only_from is None and function_info.get('keyword_only'):
            keyword_only_from = function_info.get('min_args', 0)
        
        # 检查参数数量
        if len(args) < function_info['min_args']:
            errors.append(f"函数 {function_name} 需要至少 {function_info['min_args']} 个参数，但只提供了 {len(args)}")
        elif len(args) > function_info['max_args']:
            errors.append(f"函数 {function_name} 最多接受 {function_info['max_args']} 个参数，但提供了 {len(args)}")
        
        # 处理参数验证
        # 跟踪已使用的位置参数索引
        positional_index = 0
        
        # 对于所有函数，支持命名参数
        for arg in args:
            if isinstance(arg, dict):
                if arg['type'] == 'named':
                    # 命名参数
                    if 'param_names' in function_info and arg['name'] in function_info['param_names']:
                        # 查找参数在param_names中的索引
                        param_index = function_info['param_names'].index(arg['name'])
                        if param_index < len(function_info['arg_types']):
                            expected_type = function_info['arg_types'][param_index]
                            arg_errors = self._validate_arg_type(arg['value'], expected_type, param_index, function_name, is_in_group_arg)
                            errors.extend(arg_errors)
                    # 对于winsorize函数，支持std和clip参数
                    elif function_name == 'winsorize' and arg['name'] in ['std', 'clip']:
                        arg_errors = self._validate_arg_type(arg['value'], 'number', 0, function_name, is_in_group_arg)
                        errors.extend(arg_errors)
                    # 对于bucket函数，支持'range'和'buckets'参数
                    elif function_name == 'bucket' and arg['name'] in ['range', 'buckets']:
                        # range和buckets参数应该是string类型
                        arg_errors = self._validate_arg_type(arg['value'], 'string', 1, function_name, is_in_group_arg)
                        errors.extend(arg_errors)
                    else:
                        errors.append(f"函数 {function_name} 不存在参数 '{arg['name']}'")
                elif arg['type'] == 'positional':
                    # 位置参数（字典形式）
                    if keyword_only_from is not None and positional_index >= keyword_only_from:
                        param_name = None
                        if 'param_names' in function_info and positional_index < len(function_info['param_names']):
                            param_name = function_info['param_names'][positional_index]
                        if param_name:
                            errors.append(f"函数 {function_name} 的第{positional_index+1}个参数必须使用命名参数 '{param_name}='")
                        else:
                            errors.append(f"函数 {function_name} 的第{positional_index+1}个参数必须使用命名参数")
                    else:
                        # 验证位置参数的类型
                        if positional_index < len(function_info['arg_types']):
                            expected_type = function_info['arg_types'][positional_index]
                            arg_errors = self._validate_arg_type(arg['value'], expected_type, positional_index, function_name, is_in_group_arg)
                            errors.extend(arg_errors)
                    positional_index += 1
                else:
                    # 其他字典类型参数
                    errors.append(f"参数 {positional_index+1} 格式错误")
                    positional_index += 1
            else:
                # 位置参数（直接ASTNode形式）
                if keyword_only_from is not None and positional_index >= keyword_only_from:
                    param_name = None
                    if 'param_names' in function_info and positional_index < len(function_info['param_names']):
                        param_name = function_info['param_names'][positional_index]
                    if param_name:
                        errors.append(f"函数 {function_name} 的第{positional_index+1}个参数必须使用命名参数 '{param_name}='")
                    else:
                        errors.append(f"函数 {function_name} 的第{positional_index+1}个参数必须使用命名参数")
                else:
                    # 验证位置参数的类型
                    if positional_index < len(function_info['arg_types']):
                        expected_type = function_info['arg_types'][positional_index]
                        arg_errors = self._validate_arg_type(arg, expected_type, positional_index, function_name, is_in_group_arg)
                        errors.extend(arg_errors)
                positional_index += 1
        
        return errors
    
    def _validate_arg_type(self, arg: ASTNode, expected_type: str, arg_index: int, function_name: str, is_in_group_arg: bool = False) -> List[str]:
        """验证参数类型是否符合预期"""
        errors = []

        def _is_number_like(node: ASTNode) -> bool:
            if node is None:
                return False
            if node.node_type == 'number':
                return True
            if node.node_type == 'unop' and isinstance(node.value, dict) and node.value.get('op') in {'-', '+'}:
                if node.children and hasattr(node.children[0], 'node_type'):
                    return _is_number_like(node.children[0])
            return False

        # Unit compatibility check
        # bucket()/group_cartesian_product() output a derived category (grouping key).
        # It can only be consumed where a category/grouping key is expected (typically by group_* operators).
        # It must not flow into normal Unit[] inputs like ts_mean's first argument.
        if self._is_derived_category(arg) and expected_type != 'category':
            errors.append(
                f"Incompatible unit for input of \"{function_name}\" at index {arg_index}, expected \"Unit[]\", found \"Unit[Group:1]\""
            )
            return errors
        
        # 首先检查是否是group类型字段，如果是则只能用于Group类型函数
        # 但是如果当前函数是group_xxx或在group函数的参数链中，则允许使用
        if arg.node_type == 'category' and arg.value in group_fields:
            if not (function_name.startswith('group_') or is_in_group_arg):
                errors.append(f"Group类型字段 '{arg.value}' 只能用于Group类型函数的参数中")
        
        # 然后验证参数类型是否符合预期
        if expected_type == 'expression':
            # 表达式可以是任何有效的AST节点
            pass
        elif expected_type == 'number':
            # 允许 -1 这类一元负号数字常量（解析为 unop(number)）
            if not _is_number_like(arg):
                errors.append(f"参数 {arg_index+1} 应该是一个数字，但得到 {arg.node_type}")
        elif expected_type == 'boolean':
            # 布尔值可以是 true/false 或数字（0/1）
            if arg.node_type not in {'boolean', 'number'}:
                errors.append(f"参数 {arg_index+1} 应该是一个布尔值（true/false 或 0/1），但得到 {arg.node_type}")
        elif expected_type == 'field':
            if arg.node_type != 'field' and arg.node_type != 'category':
                # 允许field或category作为字段参数
                errors.append(f"参数 {arg_index+1} 应该是一个字段，但得到 {arg.node_type}")
            elif arg.node_type == 'field' and not self._is_valid_field(arg.value):
                errors.append(f"无效的字段名: {arg.value}")
        elif expected_type == 'category':
            if not function_name.startswith('group_'):
                # 非group函数的category参数必须是category类型且在valid_categories中
                if arg.node_type != 'category':
                    errors.append(f"参数 {arg_index+1} 应该是一个类别，但得到 {arg.node_type}")
                elif arg.value not in valid_categories:
                    errors.append(f"无效的类别: {arg.value}")
            # group函数的category参数可以是任何类型（field、category等），不进行类型校验
        
        return errors

    def _infer_unit(self, node: ASTNode) -> str:
        """Infer the Unit kind of an AST node.

        Returns:
            'unit'     - regular numeric time-series Unit[]
            'scalar'   - literals (numbers/booleans/strings)
            'category' - category/grouping keys (industry/sector or derived via bucket/cartesian)
        """
        if node is None:
            return 'unit'

        cache_key = id(node)
        cached = self._unit_cache.get(cache_key)
        if cached is not None:
            return cached

        unit = 'unit'

        if node.node_type in {'number', 'boolean', 'string'}:
            unit = 'scalar'
        elif node.node_type in {'field', 'identifier'}:
            unit = 'unit'
        elif node.node_type == 'category':
            unit = 'category'
        elif node.node_type in {'unop', 'binop'}:
            child_units = [self._infer_unit(child) for child in node.children if hasattr(child, 'node_type')]
            unit = 'category' if 'category' in child_units else 'unit'
        elif node.node_type == 'function':
            fname = node.value
            # Group-building functions create derived category outputs
            if fname in {'bucket', 'group_cartesian_product'}:
                unit = 'category'
            else:
                # Default: propagate from the first positional argument if available
                first_arg = None
                for child in node.children:
                    if isinstance(child, dict):
                        if child.get('type') == 'positional':
                            first_arg = child.get('value')
                            break
                    else:
                        first_arg = child
                        break

                if hasattr(first_arg, 'node_type'):
                    unit = self._infer_unit(first_arg)
                else:
                    unit = 'unit'

        self._unit_cache[cache_key] = unit
        return unit

    def _is_derived_category(self, node: ASTNode) -> bool:
        """Return True if node is a derived category/grouping key (e.g., bucket/cartesian output)."""
        if node is None:
            return False

        cache_key = id(node)
        cached = self._derived_category_cache.get(cache_key)
        if cached is not None:
            return cached

        derived = False
        if node.node_type == 'function':
            if node.value in {'bucket', 'group_cartesian_product'}:
                derived = True
            else:
                function_info = supported_functions.get(node.value, {})
                arg_types = function_info.get('arg_types', [])
                param_names = function_info.get('param_names', [])

                positional_index = 0
                for child in node.children:
                    if isinstance(child, dict):
                        if child.get('type') == 'named':
                            name = child.get('name')
                            value = child.get('value')

                            expected_type = None
                            if name in param_names:
                                param_index = param_names.index(name)
                                if param_index < len(arg_types):
                                    expected_type = arg_types[param_index]

                            if expected_type == 'category':
                                continue

                            if self._is_derived_category(value):
                                derived = True
                                break
                        elif child.get('type') == 'positional':
                            value = child.get('value')
                            expected_type = arg_types[positional_index] if positional_index < len(arg_types) else None

                            if expected_type != 'category' and self._is_derived_category(value):
                                derived = True
                                break
                            positional_index += 1
                    else:
                        expected_type = arg_types[positional_index] if positional_index < len(arg_types) else None
                        if expected_type != 'category' and self._is_derived_category(child):
                            derived = True
                            break
                        positional_index += 1
        elif node.node_type in {'unop', 'binop'}:
            derived = any(
                self._is_derived_category(child)
                for child in node.children
                if hasattr(child, 'node_type')
            )

        self._derived_category_cache[cache_key] = derived
        return derived

    def _validate_add(self, args: List[Any], is_in_group_arg: bool = False) -> List[str]:
        """Validate add(x, y, ..., filter=false).

        Rules:
        - At least 2 positional expression terms.
        - Optional filter flag can be provided as:
          - named argument: filter=<boolean>
          - last positional argument: <boolean>
        """
        errors: List[str] = []

        if len(args) < 2:
            return [f"函数 add 需要至少 2 个参数，但只提供了 {len(args)}"]

        named_filter_nodes: List[ASTNode] = []
        positional_nodes: List[ASTNode] = []

        for arg in args:
            if isinstance(arg, dict) and arg.get('type') == 'named':
                name = arg.get('name')
                value = arg.get('value')
                if name != 'filter':
                    errors.append(f"函数 add 不存在参数 '{name}'")
                    continue
                if not hasattr(value, 'node_type'):
                    errors.append("函数 add 的参数 filter 格式错误")
                    continue
                named_filter_nodes.append(value)
            elif isinstance(arg, dict) and arg.get('type') == 'positional':
                value = arg.get('value')
                if hasattr(value, 'node_type'):
                    positional_nodes.append(value)
                else:
                    errors.append("函数 add 的位置参数格式错误")
            elif hasattr(arg, 'node_type'):
                positional_nodes.append(arg)
            else:
                errors.append("函数 add 的参数格式错误")

        if len(named_filter_nodes) > 1:
            errors.append("函数 add 的参数 'filter' 只能出现一次")

        positional_filter_node: Optional[ASTNode] = None
        # Only infer a positional filter flag when:
        # - no named filter is provided
        # - there are at least 3 positional args (x, y, filter)
        # - the last arg is boolean or numeric 0/1
        if not named_filter_nodes and len(positional_nodes) >= 3:
            last = positional_nodes[-1]
            if last.node_type == 'boolean' or (last.node_type == 'number' and last.value in {0, 1}):
                positional_filter_node = positional_nodes.pop()

        if len(positional_nodes) < 2:
            errors.append(f"函数 add 需要至少 2 个输入项（不含filter），但只提供了 {len(positional_nodes)}")

        # Validate all term inputs as expressions (no-op, but keep recursion behavior consistent)
        for idx, node in enumerate(positional_nodes):
            errors.extend(self._validate_arg_type(node, 'expression', idx, 'add', is_in_group_arg))

        # Validate filter, if present (named takes precedence; if both present, that's an error)
        if positional_filter_node is not None and named_filter_nodes:
            errors.append("函数 add 的 filter 不能同时用位置参数和命名参数传递")
        if positional_filter_node is not None:
            errors.extend(self._validate_arg_type(positional_filter_node, 'boolean', len(positional_nodes), 'add', is_in_group_arg))
        if named_filter_nodes:
            errors.extend(self._validate_arg_type(named_filter_nodes[0], 'boolean', len(positional_nodes), 'add', is_in_group_arg))

        return errors

    def _validate_winsorize(self, args: List[Any], is_in_group_arg: bool = False) -> List[str]:
        """Validate winsorize(x, std=<number>, clip=<boolean>)."""
        errors: List[str] = []
        positional_nodes: List[ASTNode] = []
        named_args: Dict[str, ASTNode] = {}

        for arg in args:
            if isinstance(arg, dict) and arg.get('type') == 'named':
                name = arg.get('name')
                value = arg.get('value')
                if name not in {'std', 'clip'}:
                    errors.append(f"函数 winsorize 不存在参数 '{name}'")
                    continue
                if name in named_args:
                    errors.append(f"函数 winsorize 的参数 '{name}' 只能出现一次")
                    continue
                if not hasattr(value, 'node_type'):
                    errors.append(f"函数 winsorize 的参数 {name} 格式错误")
                    continue
                named_args[name] = value
            elif isinstance(arg, dict) and arg.get('type') == 'positional':
                value = arg.get('value')
                if hasattr(value, 'node_type'):
                    positional_nodes.append(value)
                else:
                    errors.append("函数 winsorize 的位置参数格式错误")
            elif hasattr(arg, 'node_type'):
                positional_nodes.append(arg)
            else:
                errors.append("函数 winsorize 的参数格式错误")

        if len(positional_nodes) != 1:
            errors.append(f"Invalid number of inputs : {len(positional_nodes)}, should be exactly 1 input(s)")

        if positional_nodes:
            errors.extend(self._validate_arg_type(positional_nodes[0], 'expression', 0, 'winsorize', is_in_group_arg))
        if 'std' in named_args:
            errors.extend(self._validate_arg_type(named_args['std'], 'number', 1, 'winsorize', is_in_group_arg))
        if 'clip' in named_args:
            errors.extend(self._validate_arg_type(named_args['clip'], 'boolean', 2, 'winsorize', is_in_group_arg))

        return errors
    
    def validate_ast(self, ast: Optional[ASTNode], is_in_group_arg: bool = False) -> List[str]:
        """递归验证抽象语法树"""
        if not ast:
            return ["无法解析表达式"]
        
        errors = []
        
        # 根据节点类型进行验证
        if ast.node_type == 'function':
            # 检查当前函数是否是group函数
            is_group_function = ast.value.startswith('group_')
            # 确定当前是否在group函数的参数链中
            current_in_group_arg = is_in_group_arg or is_group_function
            # 验证函数
            function_errors = self.validate_function(ast, current_in_group_arg)
            errors.extend(function_errors)
            
            # 递归验证子节点时使用current_in_group_arg
            for child in ast.children:
                if isinstance(child, dict):
                    # 命名参数，验证其值
                    if 'value' in child and hasattr(child['value'], 'node_type'):
                        child_errors = self.validate_ast(child['value'], current_in_group_arg)
                        errors.extend(child_errors)
                elif hasattr(child, 'node_type'):
                    child_errors = self.validate_ast(child, current_in_group_arg)
                    errors.extend(child_errors)
        elif ast.node_type in ['unop', 'binop']:
            # 对操作符的子节点进行验证
            for child in ast.children:
                if hasattr(child, 'node_type'):
                    child_errors = self.validate_ast(child, is_in_group_arg)
                    errors.extend(child_errors)
        elif ast.node_type == 'field':
            # 验证字段名
            if not self._is_valid_field(ast.value):
                errors.append(f"无效的字段名: {ast.value}")
        else:
            # 递归验证子节点
            for child in ast.children:
                if isinstance(child, dict):
                    # 命名参数，验证其值
                    if 'value' in child and hasattr(child['value'], 'node_type'):
                        child_errors = self.validate_ast(child['value'], is_in_group_arg)
                        errors.extend(child_errors)
                elif hasattr(child, 'node_type'):
                    child_errors = self.validate_ast(child, is_in_group_arg)
                    errors.extend(child_errors)
        
        return errors
    
    def _process_semicolon_expression(self, expression: str) -> Tuple[bool, str]:
        """处理带有分号的表达式，将其转换为不带分号的简化形式
        
        Args:
            expression: 要处理的表达式字符串
            
        Returns:
            Tuple[bool, str]: (是否成功, 转换后的表达式或错误信息)
        """
        def _top_level_equals_positions(stmt: str) -> List[int]:
            """返回所有“顶层赋值”等号位置。

            仅统计括号外（()[]{})、引号外、且不属于比较操作符(==,!=,<=,>=)的 '='。
            这样可以避免把关键字参数（如 rettype=0）误判为赋值语句。
            """
            positions: List[int] = []
            paren_depth = 0
            bracket_depth = 0
            brace_depth = 0
            in_single_quote = False
            in_double_quote = False
            escape = False

            for i, ch in enumerate(stmt):
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue

                if in_single_quote:
                    if ch == "'":
                        in_single_quote = False
                    continue
                if in_double_quote:
                    if ch == '"':
                        in_double_quote = False
                    continue

                if ch == "'":
                    in_single_quote = True
                    continue
                if ch == '"':
                    in_double_quote = True
                    continue

                if ch == '(':
                    paren_depth += 1
                    continue
                if ch == ')':
                    paren_depth = max(0, paren_depth - 1)
                    continue
                if ch == '[':
                    bracket_depth += 1
                    continue
                if ch == ']':
                    bracket_depth = max(0, bracket_depth - 1)
                    continue
                if ch == '{':
                    brace_depth += 1
                    continue
                if ch == '}':
                    brace_depth = max(0, brace_depth - 1)
                    continue

                if paren_depth or bracket_depth or brace_depth:
                    continue

                if ch != '=':
                    continue

                prev_ch = stmt[i - 1] if i > 0 else ''
                next_ch = stmt[i + 1] if i + 1 < len(stmt) else ''
                if prev_ch in ['=', '!', '<', '>'] or next_ch == '=':
                    continue

                positions.append(i)

            return positions

        def _keyword_arg_names(stmt: str):
            """提取函数调用中的命名参数名（如 rettype=0 中的 rettype）。

            只收集括号/中括号/大括号内部出现的 name= 形式，避免把脚本级赋值误当作命名参数。
            """
            names = set()
            paren_depth = 0
            bracket_depth = 0
            brace_depth = 0
            in_single_quote = False
            in_double_quote = False
            escape = False

            i = 0
            while i < len(stmt):
                ch = stmt[i]

                if escape:
                    escape = False
                    i += 1
                    continue
                if ch == '\\':
                    escape = True
                    i += 1
                    continue

                if in_single_quote:
                    if ch == "'":
                        in_single_quote = False
                    i += 1
                    continue
                if in_double_quote:
                    if ch == '"':
                        in_double_quote = False
                    i += 1
                    continue

                if ch == "'":
                    in_single_quote = True
                    i += 1
                    continue
                if ch == '"':
                    in_double_quote = True
                    i += 1
                    continue

                if ch == '(':
                    paren_depth += 1
                    i += 1
                    continue
                if ch == ')':
                    paren_depth = max(0, paren_depth - 1)
                    i += 1
                    continue
                if ch == '[':
                    bracket_depth += 1
                    i += 1
                    continue
                if ch == ']':
                    bracket_depth = max(0, bracket_depth - 1)
                    i += 1
                    continue
                if ch == '{':
                    brace_depth += 1
                    i += 1
                    continue
                if ch == '}':
                    brace_depth = max(0, brace_depth - 1)
                    i += 1
                    continue

                inside_container = bool(paren_depth or bracket_depth or brace_depth)

                if inside_container and (ch.isalpha() or ch == '_'):
                    start = i
                    i += 1
                    while i < len(stmt) and (stmt[i].isalnum() or stmt[i] == '_'):
                        i += 1
                    name = stmt[start:i]

                    j = i
                    while j < len(stmt) and stmt[j].isspace():
                        j += 1

                    if j < len(stmt) and stmt[j] == '=':
                        next_ch = stmt[j + 1] if j + 1 < len(stmt) else ''
                        if next_ch != '=':
                            names.add(name.lower())
                    continue

                i += 1

            return names

        # 检查表达式是否以分号结尾
        if expression.strip().endswith(';'):
            return False, "表达式不能以分号结尾"
        
        # 分割表达式为语句列表
        statements = [stmt.strip() for stmt in expression.split(';') if stmt.strip()]
        if not statements:
            return False, "表达式不能为空"
        
        # 存储变量赋值
        variables = {}
        
        # 处理每个赋值语句（除了最后一个）
        for i, stmt in enumerate(statements[:-1]):
            eq_positions = _top_level_equals_positions(stmt)
            if not eq_positions:
                return False, f"第{i+1}个语句必须是赋值语句（使用=符号）"
            if len(eq_positions) > 1:
                return False, f"第{i+1}个语句只能包含一个赋值符号（=）"

            real_equals_pos = eq_positions[0]
            
            # 分割变量名和值
            var_name = stmt[:real_equals_pos].strip()
            var_value = stmt[real_equals_pos + 1:].strip()
            
            # 检查变量名是否有效
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                return False, f"第{i+1}个语句的变量名'{var_name}'无效，只能包含字母、数字和下划线，且不能以数字开头"
            
            var_name_lower = var_name.lower()  # 变量名不区分大小写
            
            # 检查变量名是否在后续表达式中使用
            # 这里不需要，因为后面的表达式会检查
            
            # 检查变量值中使用的变量是否已经定义
            # 简单检查：提取所有可能的变量名
            kw_names = _keyword_arg_names(var_value)
            used_vars = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', var_value)
            for used_var in used_vars:
                used_var_lower = used_var.lower()
                if used_var_lower in kw_names:
                    continue
                if used_var_lower not in variables:
                    # 检查是否是函数名
                    if used_var not in supported_functions:
                        # 对于单个字母或简单单词，不自动视为字段名，要求先定义
                        if len(used_var) <= 2:
                            return False, f"第{i+1}个语句中使用的变量'{used_var}'未在之前定义"
                        # 对于较长的字段名，仍然允许作为字段名
                        elif not self._is_valid_field(used_var):
                            return False, f"第{i+1}个语句中使用的变量'{used_var}'未在之前定义"
            
            # 将之前定义的变量替换到当前值中
            for existing_var, existing_val in variables.items():
                # 使用单词边界匹配，避免替换到其他单词的一部分
                var_value = re.sub(rf'\b{existing_var}\b', existing_val, var_value)
            
            # 存储变量
            variables[var_name_lower] = var_value
        
        # 处理最后一个语句（实际的表达式）
        final_stmt = statements[-1]
        
        # 检查最后一个语句是否是赋值语句
        if _top_level_equals_positions(final_stmt):
            return False, "最后一个语句不能是赋值语句"
        
        # 检查最后一个语句中使用的变量是否已经定义
        kw_names = _keyword_arg_names(final_stmt)
        used_vars = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', final_stmt)
        for used_var in used_vars:
            used_var_lower = used_var.lower()
            if used_var_lower in kw_names:
                continue
            if used_var_lower not in variables:
                # 检查是否是函数名
                if used_var not in supported_functions:
                    # 对于单个字母或简单单词，不自动视为字段名，要求先定义
                    if len(used_var) <= 2:
                        return False, f"最后一个语句中使用的变量'{used_var}'未在之前定义"

                    # 允许直接使用字段名/类别名（如 close/industry）
                    if self._is_valid_field(used_var) or used_var_lower in valid_categories or used_var_lower in group_fields:
                        continue

                    return False, f"最后一个语句中使用的变量'{used_var}'未在之前定义"
        
        # 将变量替换到最后一个表达式中
        final_expr = final_stmt
        for var_name, var_value in variables.items():
            final_expr = re.sub(rf'\b{var_name}\b', var_value, final_expr)
        
        return True, final_expr
    
    def check_expression(self, expression: str) -> Dict[str, Any]:
        """
        检查表达式格式是否正确
        
        Args:
            expression: 要验证的表达式字符串
            
        Returns:
            包含验证结果的字典
        """
        # 重置错误列表
        self.errors = []
        # Reset unit inference cache for this expression
        self._unit_cache = {}
        self._derived_category_cache = {}
        
        try:
            expression = expression.strip()
            if not expression:
                return {
                    'valid': False,
                    'errors': ['表达式不能为空'],
                    'tokens': [],
                    'ast': None
                }
            
            # 处理带有分号的表达式
            if ';' in expression:
                success, result = self._process_semicolon_expression(expression)
                if not success:
                    return {
                        'valid': False,
                        'errors': [result],
                        'tokens': [],
                        'ast': None
                    }
                expression = result
            
            # 重置词法分析器的行号
            self.lexer.lineno = 1
            
            # 词法分析（用于调试）
            self.lexer.input(expression)
            tokens = []
            # 调试：打印识别的标记
            # print(f"\n调试 - 表达式: {expression}")
            # print("识别的标记:")
            for token in self.lexer:
                # print(f"  - 类型: {token.type}, 值: '{token.value}', 位置: {token.lexpos}")
                tokens.append(token)
            
            # 重新设置词法分析器的输入，以便语法分析器使用
            self.lexer.input(expression)
            self.lexer.lineno = 1
            
            # 语法分析
            ast = self.parser.parse(expression, lexer=self.lexer)
            
            # 验证AST
            validation_errors = self.validate_ast(ast)
            
            # 合并所有错误
            all_errors = self.errors + validation_errors
            
            # 检查括号是否匹配
            bracket_count = 0
            for char in expression:
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
                if bracket_count < 0:
                    all_errors.append("括号不匹配: 右括号过多")
                    break
            if bracket_count > 0:
                all_errors.append("括号不匹配: 左括号过多")
            
            return {
                'valid': len(all_errors) == 0,
                'errors': all_errors,
                'tokens': tokens,
                'ast': ast
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"解析错误: {str(e)}"],
                'tokens': [],
                'ast': None
            }



