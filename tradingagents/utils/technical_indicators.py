"""
技术指标计算工具
包括 KDJ, RSI, MACD 等常见技术指标
"""

import numpy as np
from tradingagents.utils.logging_init import get_logger

logger = get_logger("technical_indicators")


def calculate_kdj(high_array, low_array, close_array, kperiods=14, dperiods=3):
    """
    计算 KDJ 指标
    
    Args:
        high_array: 最高价数组
        low_array: 最低价数组
        close_array: 收盘价数组
        kperiods: K 周期（默认14）
        dperiods: D 周期（默认3）
    
    Returns:
        dict: 包含 K值、D值、J值及相关指标的字典
    """
    try:
        high_array = np.array(high_array)
        low_array = np.array(low_array)
        close_array = np.array(close_array)
        
        if len(high_array) < kperiods:
            logger.warning(f"⚠️ 数据不足以计算KDJ (需要至少 {kperiods} 根K线，实际 {len(high_array)} 根)")
            return None
        
        # 计算最高价和最低价
        array_highest = []
        array_lowest = []
        
        for x in range(len(high_array) - kperiods):
            highest = max(high_array[x:x+kperiods])
            lowest = min(low_array[x:x+kperiods])
            array_highest.append(highest)
            array_lowest.append(lowest)
        
        # 计算 K 值
        kvalue = []
        for x in range(kperiods, len(close_array)):
            if array_highest[x-kperiods] == array_lowest[x-kperiods]:
                k = 50  # 避免除以零
            else:
                k = ((close_array[x] - array_lowest[x-kperiods]) * 100 / 
                     (array_highest[x-kperiods] - array_lowest[x-kperiods]))
            kvalue.append(k)
        
        # 计算 D 值 (K值的3日移动平均)
        dvalue = [None, None]
        for x in range(len(kvalue) - dperiods + 1):
            d = sum(kvalue[x:x+dperiods]) / dperiods
            dvalue.append(d)
        
        # 计算 J 值 (3*K - 2*D)
        jvalue = [None, None]
        for x in range(len(dvalue) - dperiods + 1):
            if dvalue[x+2] is not None and x+2 < len(kvalue):
                j = (dvalue[x+2] * 3) - (kvalue[x+2] * 2)
                jvalue.append(j)
        
        # 获取最新值
        latest_k = kvalue[-1] if kvalue else None
        latest_d = dvalue[-1] if dvalue[-1] is not None else None
        latest_j = jvalue[-1] if jvalue[-1] is not None else None
        
        logger.info(f"✅ KDJ 计算完成: K={latest_k:.2f}, D={latest_d:.2f}, J={latest_j:.2f}")
        
        return {
            "k_values": kvalue,
            "d_values": dvalue,
            "j_values": jvalue,
            "latest_k": latest_k,
            "latest_d": latest_d,
            "latest_j": latest_j,
            "signal": analyze_kdj_signal(latest_k, latest_d, latest_j)
        }
    
    except Exception as e:
        logger.error(f"❌ KDJ 计算失败: {e}")
        return None


def analyze_kdj_signal(k, d, j):
    """
    分析 KDJ 信号
    
    Args:
        k: K值
        d: D值
        j: J值
    
    Returns:
        str: 信号描述
    """
    if k is None or d is None:
        return "数据不足"
    
    signals = []
    
    # K > D 且都 > 50: 强势上升
    if k > d and k > 50 and d > 50:
        signals.append("强势上升信号")
    # K > D 且都 < 50: 弱势上升信号
    elif k > d and k < 50:
        signals.append("弱势上升信号")
    # K < D 且都 < 50: 强势下跌
    elif k < d and k < 50 and d < 50:
        signals.append("强势下跌信号")
    # K < D 且都 > 50: 弱势下跌信号
    elif k < d and k > 50:
        signals.append("弱势下跌信号")
    
    # J值超过上限或下限
    if j > 100:
        signals.append("J值超过上限(100)，可能过热")
    elif j < 0:
        signals.append("J值超过下限(0)，可能过冷")
    
    # 金叉 / 死叉检测
    if k > 80 and d > 80:
        signals.append("超买区域")
    elif k < 20 and d < 20:
        signals.append("超卖区域")
    
    return " | ".join(signals) if signals else "中立"
