"""
股票分析执行工具
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger, get_logger_manager
logger = get_logger('backend')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 确保环境变量正确加载
load_dotenv(project_root / ".env", override=True)

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_web_logging
logger = setup_web_logging()

# 添加配置管理器
try:
    from tradingagents.config.config_manager import token_tracker
    TOKEN_TRACKING_ENABLED = True
    logger.info("✅ Token跟踪功能已启用")
except ImportError:
    TOKEN_TRACKING_ENABLED = False
    logger.warning("⚠️ Token跟踪功能未启用")

def translate_analyst_labels(text):
    """将分析师的英文标签转换为中文"""
    if not text:
        return text

    # 分析师标签翻译映射
    translations = {
        'Bull Analyst:': '看涨分析师:',
        'Bear Analyst:': '看跌分析师:',
        'Risky Analyst:': '激进风险分析师:',
        'Safe Analyst:': '保守风险分析师:',
        'Neutral Analyst:': '中性风险分析师:',
        'Research Manager:': '研究经理:',
        'Portfolio Manager:': '投资组合经理:',
        'Risk Judge:': '风险管理委员会:',
        'Trader:': '交易员:'
    }

    # 替换所有英文标签
    for english, chinese in translations.items():
        text = text.replace(english, chinese)

    return text

def extract_risk_assessment(state):
    """从分析状态中提取风险评估数据"""
    try:
        risk_debate_state = state.get('risk_debate_state', {})

        if not risk_debate_state:
            return None

        # 提取各个风险分析师的观点并进行中文化
        risky_analysis = translate_analyst_labels(risk_debate_state.get('risky_history', ''))
        safe_analysis = translate_analyst_labels(risk_debate_state.get('safe_history', ''))
        neutral_analysis = translate_analyst_labels(risk_debate_state.get('neutral_history', ''))
        judge_decision = translate_analyst_labels(risk_debate_state.get('judge_decision', ''))

        # 格式化风险评估报告
        risk_assessment = f"""
## ⚠️ 风险评估报告

### 🔴 激进风险分析师观点
{risky_analysis if risky_analysis else '暂无激进风险分析'}

### 🟡 中性风险分析师观点
{neutral_analysis if neutral_analysis else '暂无中性风险分析'}

### 🟢 保守风险分析师观点
{safe_analysis if safe_analysis else '暂无保守风险分析'}

### 🏛️ 风险管理委员会最终决议
{judge_decision if judge_decision else '暂无风险管理决议'}

---
*风险评估基于多角度分析，请结合个人风险承受能力做出投资决策*
        """.strip()

        return risk_assessment

    except Exception as e:
        logger.info(f"提取风险评估数据时出错: {e}")
        return None

def run_stock_analysis(stock_symbol, analysis_date, analysts, research_depth, market_type="美股", llm_provider=None, include_risk_assessment=True, progress_callback=None):
    """执行股票分析

    Args:
        stock_symbol: 股票代码
        analysis_date: 分析日期
        analysts: 分析师列表
        research_depth: 研究深度
        market_type: 市场类型 (美股/A股/港股)
        llm_provider: LLM提供商 (dashscope/deepseek/google/openai)
        include_risk_assessment: 是否包含风险评估
        progress_callback: 进度回调函数，用于更新UI状态
    """

    def update_progress(message, step=None, total_steps=None):
        """更新进度"""
        if progress_callback:
            progress_callback(message, step, total_steps)
        logger.info(f"[进度] {message}")

    # 生成会话ID用于Token跟踪和日志关联
    session_id = f"analysis_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 1. 数据预获取和验证阶段
    update_progress("🔍 验证股票代码并预获取数据...", 1, 10)

    try:
        from tradingagents.utils.stock_validator import prepare_stock_data

        # 预获取股票数据（默认30天历史数据）
        preparation_result = prepare_stock_data(
            stock_code=stock_symbol,
            market_type=market_type,
            period_days=30,  # 可以根据research_depth调整
            analysis_date=analysis_date
        )

        if not preparation_result.is_valid:
            error_msg = f"❌ 股票数据验证失败: {preparation_result.error_message}"
            update_progress(error_msg)
            logger.error(f"[{session_id}] {error_msg}")

            return {
                'success': False,
                'error': preparation_result.error_message,
                'suggestion': preparation_result.suggestion,
                'stock_symbol': stock_symbol,
                'analysis_date': analysis_date,
                'session_id': session_id
            }

        # 数据预获取成功
        success_msg = f"✅ 数据准备完成: {preparation_result.stock_name} ({preparation_result.market_type})"
        update_progress(success_msg)  # 使用智能检测，不再硬编码步骤
        logger.info(f"[{session_id}] {success_msg}")
        logger.info(f"[{session_id}] 缓存状态: {preparation_result.cache_status}")

    except Exception as e:
        error_msg = f"❌ 数据预获取过程中发生错误: {str(e)}"
        update_progress(error_msg)
        logger.error(f"[{session_id}] {error_msg}")

        return {
            'success': False,
            'error': error_msg,
            'suggestion': "请检查网络连接或稍后重试",
            'stock_symbol': stock_symbol,
            'analysis_date': analysis_date,
            'session_id': session_id
        }

    # 记录分析开始的详细日志
    logger_manager = get_logger_manager()
    import time
    analysis_start_time = time.time()

    logger_manager.log_analysis_start(
        logger, stock_symbol, "comprehensive_analysis", session_id
    )

    # 尽早确定LLM提供商，以便日志和后续步骤使用
    # 优先使用传入的参数，其次默认值
    if not llm_provider:
        llm_provider = 'dashscope' if market_type in ['A股', '港股'] else 'google'
    
    logger.info(f"✅ [LLM提供商] 已确定: {llm_provider}，市场类型: {market_type}")

    logger.info(f"🚀 [分析开始] 股票分析启动",
               extra={
                   'stock_symbol': stock_symbol,
                   'analysis_date': analysis_date,
                   'analysts': analysts,
                   'research_depth': research_depth,
                   'llm_provider': llm_provider,
                   'market_type': market_type,
                   'session_id': session_id,
                   'event_type': 'web_analysis_start'
               })

    update_progress("🚀 开始股票分析...")

    # 估算Token使用（用于成本预估）
    if TOKEN_TRACKING_ENABLED:
        estimated_input = 2000 * len(analysts)  # 估算每个分析师2000个输入token
        estimated_output = 1000 * len(analysts)  # 估算每个分析师1000个输出token
        estimated_cost = token_tracker.estimate_cost(llm_provider, None, estimated_input, estimated_output)

        update_progress(f"💰 预估分析成本: ¥{estimated_cost:.4f}")

    # 验证环境变量
    update_progress("检查环境变量配置...")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    finnhub_key = os.getenv("FINNHUB_API_KEY")

    logger.info(f"环境变量检查:")
    logger.info(f"  DASHSCOPE_API_KEY: {'已设置' if dashscope_key else '未设置'}")
    logger.info(f"  FINNHUB_API_KEY: {'已设置' if finnhub_key else '未设置'}")

    if not dashscope_key:
        raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")
    if not finnhub_key:
        raise ValueError("FINNHUB_API_KEY 环境变量未设置")

    update_progress("环境变量验证通过")

    try:
        # 导入必要的模块
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        # 创建配置
        update_progress("配置分析参数...")
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = llm_provider
        config["deep_think_llm"] = None
        config["quick_think_llm"] = None
        
        # 处理风险评估配置
        if not include_risk_assessment:
            logger.info("🚫 风险评估已根据用户请求禁用")
            config["max_risk_discuss_rounds"] = 0
            
        # 根据研究深度调整配置
        if research_depth == 1:  # 1级 - 快速分析
            config["max_debate_rounds"] = 1
            if include_risk_assessment:
                config["max_risk_discuss_rounds"] = 1
            # 保持内存功能启用，因为内存操作开销很小但能显著提升分析质量
            config["memory_enabled"] = True

            # 统一使用在线工具，避免离线工具的各种问题
            config["online_tools"] = True  # 所有市场都使用统一工具
            logger.info(f"🔧 [快速分析] {market_type}使用统一工具，确保数据源正确和稳定性")
            if llm_provider == "dashscope":
                config["quick_think_llm"] = "qwen-turbo"  # 使用最快模型
                config["deep_think_llm"] = "qwen-plus"
            elif llm_provider == "deepseek":
                config["quick_think_llm"] = "deepseek-chat"  # DeepSeek只有一个模型
                config["deep_think_llm"] = "deepseek-chat"
        elif research_depth == 2:  # 2级 - 基础分析
            config["max_debate_rounds"] = 1
            if include_risk_assessment:
                config["max_risk_discuss_rounds"] = 1
            config["memory_enabled"] = True
            config["online_tools"] = True
            if llm_provider == "dashscope":
                config["quick_think_llm"] = "qwen-plus"
                config["deep_think_llm"] = "qwen-plus"
            elif llm_provider == "deepseek":
                config["quick_think_llM"] = "deepseek-chat"
                config["deep_think_llm"] = "deepseek-chat"
            elif llm_provider == "openai":
                config["quick_think_llm"] = "gpt-4o-mini"
                config["deep_think_llm"] = "gpt-4o"
            elif llm_provider == "google":
                config["quick_think_llm"] = "gemini-2.0-flash"
                config["deep_think_llm"] = "gemini-2.5-flash"
        elif research_depth == 3:  # 3级 - 标准分析 (默认)
            config["max_debate_rounds"] = 1
            if include_risk_assessment:
                config["max_risk_discuss_rounds"] = 2
            config["memory_enabled"] = True
            config["online_tools"] = True
            if llm_provider == "dashscope":
                config["quick_think_llm"] = "qwen-plus"
                config["deep_think_llm"] = "qwen3-max"
            elif llm_provider == "deepseek":
                config["quick_think_llm"] = "deepseek-chat"
                config["deep_think_llm"] = "deepseek-chat"
            elif llm_provider == "openai":
                config["quick_think_llm"] = "gpt-4o"
                config["deep_think_llm"] = "gpt-4o"
            elif llm_provider == "google":
                config["quick_think_llm"] = "gemini-2.5-flash"
                config["deep_think_llm"] = "gemini-2.5-flash"
        elif research_depth == 4:  # 4级 - 深度分析
            config["max_debate_rounds"] = 2
            if include_risk_assessment:
                config["max_risk_discuss_rounds"] = 2
            config["memory_enabled"] = True
            config["online_tools"] = True
            if llm_provider == "dashscope":
                config["quick_think_llm"] = "qwen-plus"
                config["deep_think_llm"] = "qwen3-max"
            elif llm_provider == "deepseek":
                config["quick_think_llm"] = "deepseek-chat"
                config["deep_think_llm"] = "deepseek-chat"
            elif llm_provider == "openai":
                config["quick_think_llm"] = "gpt-4o"
                config["deep_think_llm"] = "gpt-4o"
            elif llm_provider == "google":
                config["quick_think_llm"] = "gemini-2.5-pro"
                config["deep_think_llm"] = "gemini-2.5-pro"

        # 根据LLM提供商设置不同的配置
        if llm_provider == "dashscope":
            config["backend_url"] = "https://dashscope.aliyuncs.com/api/v1"
        elif llm_provider == "deepseek":
            config["backend_url"] = "https://api.deepseek.com"
        elif llm_provider == "google":
            # Google AI使用Google官方端点
            config["backend_url"] = "https://generativelanguage.googleapis.com"
            
            # 根据研究深度优化Google模型选择（限制在核心三款模型内）
            if research_depth == 1:  # 快速分析 - 使用最快模型
                config["quick_think_llm"] = "gemini-2.5-flash"
                config["deep_think_llm"] = "gemini-2.0-flash"
            elif research_depth == 2:  # 基础分析 - 平衡速度与质量
                config["quick_think_llm"] = "gemini-2.0-flash"
                config["deep_think_llm"] = "gemini-2.5-flash"
            elif research_depth == 3:  # 标准分析 - 双Flash平衡组合
                config["quick_think_llm"] = "gemini-2.5-flash"
                config["deep_think_llm"] = "gemini-2.5-flash"
            else:  # 深度分析 - 使用Pro获取最高质量
                config["quick_think_llm"] = "gemini-2.5-flash"
                config["deep_think_llm"] = "gemini-2.5-pro"
            
            logger.info(f"🤖 [Google AI] 快速模型: {config['quick_think_llm']}")
            logger.info(f"🤖 [Google AI] 深度模型: {config['deep_think_llm']}")
        elif llm_provider == "openai":
            # OpenAI官方API
            config["backend_url"] = "https://api.openai.com/v1"
            logger.info("🤖 [OpenAI] 使用推荐模型组合：快速 gpt-4o-mini，深度 gpt-4o")
            logger.info(f"🤖 [OpenAI] API端点: https://api.openai.com/v1")
        elif llm_provider == "openrouter":
            # OpenRouter使用OpenAI兼容API
            config["backend_url"] = "https://openrouter.ai/api/v1"
            logger.info("🌐 [OpenRouter] 集成已禁用")
            logger.info(f"🌐 [OpenRouter] API端点: https://openrouter.ai/api/v1")
        elif llm_provider == "siliconflow":
            config["backend_url"] = "https://api.siliconflow.cn/v1"
            logger.info("🌐 [SiliconFlow] 集成已禁用")
            logger.info(f"🌐 [SiliconFlow] API端点: https://api.siliconflow.cn/v1")
        elif llm_provider == "custom_openai":
            # 自定义OpenAI端点 - 这里的配置通常来自前端，如果没有则使用默认
            custom_base_url = "https://api.openai.com/v1"
            config["backend_url"] = custom_base_url
            config["custom_openai_base_url"] = custom_base_url
            logger.info("🔧 [自定义OpenAI] 集成已禁用")
            logger.info(f"🔧 [自定义OpenAI] API端点: {custom_base_url}")

        # 修复路径问题 - 优先使用环境变量配置
        # 数据目录：优先使用环境变量，否则使用默认路径
        if not config.get("data_dir") or config["data_dir"] == "./data":
            env_data_dir = os.getenv("TRADINGAGENTS_DATA_DIR")
            if env_data_dir:
                # 如果环境变量是相对路径，相对于项目根目录解析
                if not os.path.isabs(env_data_dir):
                    config["data_dir"] = str(project_root / env_data_dir)
                else:
                    config["data_dir"] = env_data_dir
            else:
                config["data_dir"] = str(project_root / "data")

        # 结果目录：优先使用环境变量，否则使用默认路径
        if not config.get("results_dir") or config["results_dir"] == "./results":
            env_results_dir = os.getenv("TRADINGAGENTS_RESULTS_DIR")
            if env_results_dir:
                # 如果环境变量是相对路径，相对于项目根目录解析
                if not os.path.isabs(env_results_dir):
                    config["results_dir"] = str(project_root / env_results_dir)
                else:
                    config["results_dir"] = env_results_dir
            else:
                config["results_dir"] = str(project_root / "results")

        # 缓存目录：优先使用环境变量，否则使用默认路径
        if not config.get("data_cache_dir"):
            env_cache_dir = os.getenv("TRADINGAGENTS_CACHE_DIR")
            if env_cache_dir:
                # 如果环境变量是相对路径，相对于项目根目录解析
                if not os.path.isabs(env_cache_dir):
                    config["data_cache_dir"] = str(project_root / env_cache_dir)
                else:
                    config["data_cache_dir"] = env_cache_dir
            else:
                config["data_cache_dir"] = str(project_root / "tradingagents" / "dataflows" / "data_cache")

        # 确保目录存在
        update_progress("📁 创建必要的目录...")
        os.makedirs(config["data_dir"], exist_ok=True)
        os.makedirs(config["results_dir"], exist_ok=True)
        os.makedirs(config["data_cache_dir"], exist_ok=True)

        logger.info(f"📁 目录配置:")
        logger.info(f"  - 数据目录: {config['data_dir']}")
        logger.info(f"  - 结果目录: {config['results_dir']}")
        logger.info(f"  - 缓存目录: {config['data_cache_dir']}")
        logger.info(f"  - 环境变量 TRADINGAGENTS_RESULTS_DIR: {os.getenv('TRADINGAGENTS_RESULTS_DIR', '未设置')}")

        logger.info(f"使用配置: {config}")
        logger.info(f"分析师列表: {analysts}")
        logger.info(f"股票代码: {stock_symbol}")
        logger.info(f"分析日期: {analysis_date}")

        # 根据市场类型调整股票代码格式
        logger.debug(f"🔍 [RUNNER DEBUG] ===== 股票代码格式化 =====")
        logger.debug(f"🔍 [RUNNER DEBUG] 原始股票代码: '{stock_symbol}'")
        logger.debug(f"🔍 [RUNNER DEBUG] 市场类型: '{market_type}'")

        if market_type == "A股":
            # A股代码不需要特殊处理，保持原样
            formatted_symbol = stock_symbol
            logger.debug(f"🔍 [RUNNER DEBUG] A股代码保持原样: '{formatted_symbol}'")
            update_progress(f"🇨🇳 准备分析A股: {formatted_symbol}")
        elif market_type == "港股":
            # 港股代码转为大写，确保.HK后缀
            formatted_symbol = stock_symbol.upper()
            if not formatted_symbol.endswith('.HK'):
                # 如果是纯数字，添加.HK后缀
                if formatted_symbol.isdigit():
                    formatted_symbol = f"{formatted_symbol.zfill(4)}.HK"
            update_progress(f"🇭🇰 准备分析港股: {formatted_symbol}")
        else:
            # 美股代码转为大写
            formatted_symbol = stock_symbol.upper()
            logger.debug(f"🔍 [RUNNER DEBUG] 美股代码转大写: '{stock_symbol}' -> '{formatted_symbol}'")
            update_progress(f"🇺🇸 准备分析美股: {formatted_symbol}")

        logger.debug(f"🔍 [RUNNER DEBUG] 最终传递给分析引擎的股票代码: '{formatted_symbol}'")

        # 初始化交易图
        update_progress("🔧 初始化分析引擎...")
        graph = TradingAgentsGraph(analysts, config=config, debug=False)

        # 执行分析
        update_progress(f"📊 开始分析 {formatted_symbol} 股票，这可能需要几分钟时间...")
        logger.debug(f"🔍 [RUNNER DEBUG] ===== 调用graph.propagate =====")
        logger.debug(f"🔍 [RUNNER DEBUG] 传递给graph.propagate的参数:")
        logger.debug(f"🔍 [RUNNER DEBUG]   symbol: '{formatted_symbol}'")
        logger.debug(f"🔍 [RUNNER DEBUG]   date: '{analysis_date}'")

        state, decision = graph.propagate(formatted_symbol, analysis_date)

        # 调试信息
        logger.debug(f"🔍 [DEBUG] 分析完成，decision类型: {type(decision)}")
        logger.debug(f"🔍 [DEBUG] decision内容: {decision}")

        # 格式化结果
        update_progress("📋 分析完成，正在整理结果...")

        # 提取风险评估数据
        risk_assessment = extract_risk_assessment(state)

        # 将风险评估添加到状态中
        if risk_assessment:
            state['risk_assessment'] = risk_assessment

        # 记录Token使用（实际使用量，这里使用估算值）
        if TOKEN_TRACKING_ENABLED:
            # 在实际应用中，这些值应该从LLM响应中获取
            # 这里使用基于分析师数量和研究深度的估算
            actual_input_tokens = len(analysts) * (1500 if research_depth == 1 else 2200 if research_depth == 2 else 3000 if research_depth == 3 else 4200)
            actual_output_tokens = len(analysts) * (800 if research_depth == 1 else 1100 if research_depth == 2 else 1500 if research_depth == 3 else 2200)

            usage_record = token_tracker.track_usage(
                provider=llm_provider,
                model_name=config.get("deep_think_llm"),
                input_tokens=actual_input_tokens,
                output_tokens=actual_output_tokens,
                session_id=session_id,
                analysis_type=f"{market_type}_analysis"
            )

            if usage_record:
                update_progress(f"💰 记录使用成本: ¥{usage_record.cost:.4f}")

        results = {
            'stock_symbol': stock_symbol,
            'analysis_date': analysis_date,
            'analysts': analysts,
            'research_depth': research_depth,
            'llm_provider': llm_provider,
            'llm_model': config.get('deep_think_llm'),
            'state': state,
            'decision': decision,
            'success': True,
            'error': None,
            'session_id': session_id if TOKEN_TRACKING_ENABLED else None
        }

        # 记录分析完成的详细日志
        analysis_duration = time.time() - analysis_start_time

        # 计算总成本（如果有Token跟踪）
        total_cost = 0.0
        if TOKEN_TRACKING_ENABLED:
            try:
                total_cost = token_tracker.get_session_cost(session_id)
            except:
                pass

        logger_manager.log_analysis_complete(
            logger, stock_symbol, "comprehensive_analysis", session_id,
            analysis_duration, total_cost
        )

        logger.info(f"✅ [分析完成] 股票分析成功完成",
                   extra={
                       'stock_symbol': stock_symbol,
                       'session_id': session_id,
                       'duration': analysis_duration,
                       'total_cost': total_cost,
                       'analysts_used': analysts,
                       'success': True,
                       'event_type': 'web_analysis_complete'
                   })

        # 保存分析报告到本地和MongoDB
        try:
            update_progress("💾 正在保存分析报告...")
            from .report_exporter import save_analysis_report, save_modular_reports_to_results_dir
            
            # 1. 保存分模块报告到本地目录
            logger.info(f"📁 [本地保存] 开始保存分模块报告到本地目录")
            local_files = save_modular_reports_to_results_dir(results, stock_symbol)
            if local_files:
                logger.info(f"✅ [本地保存] 已保存 {len(local_files)} 个本地报告文件")
                for module, path in local_files.items():
                    logger.info(f"  - {module}: {path}")
            else:
                logger.warning(f"⚠️ [本地保存] 本地报告文件保存失败")
            
            # 2. 保存分析报告到MongoDB
            logger.info(f"🗄️ [MongoDB保存] 开始保存分析报告到MongoDB")
            save_success = save_analysis_report(
                stock_symbol=stock_symbol,
                analysis_results=results
            )
            
            if save_success:
                logger.info(f"✅ [MongoDB保存] 分析报告已成功保存到MongoDB")
                update_progress("✅ 分析报告已保存到数据库和本地文件")
            else:
                logger.warning(f"⚠️ [MongoDB保存] MongoDB报告保存失败")
                if local_files:
                    update_progress("✅ 本地报告已保存，但数据库保存失败")
                else:
                    update_progress("⚠️ 报告保存失败，但分析已完成")
                
        except Exception as save_error:
            logger.error(f"❌ [报告保存] 保存分析报告时发生错误: {str(save_error)}")
            update_progress("⚠️ 报告保存出错，但分析已完成")

        update_progress("✅ 分析成功完成！")
        return results

    except Exception as e:
        # 记录分析失败的详细日志
        analysis_duration = time.time() - analysis_start_time

        logger_manager.log_module_error(
            logger, "comprehensive_analysis", stock_symbol, session_id,
            analysis_duration, str(e)
        )

        logger.error(f"❌ [分析失败] 股票分析执行失败",
                    extra={
                        'stock_symbol': stock_symbol,
                        'session_id': session_id,
                        'duration': analysis_duration,
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'analysts_used': analysts,
                        'success': False,
                        'event_type': 'web_analysis_error'
                    }, exc_info=True)

        # 如果真实分析失败，返回错误信息而不是误导性演示数据
        return {
            'stock_symbol': stock_symbol,
            'analysis_date': analysis_date,
            'analysts': analysts,
            'research_depth': research_depth,
            'llm_provider': llm_provider,
            'llm_model': config.get('deep_think_llm'),
            'state': {},  # 空状态，将显示占位符
            'decision': {},  # 空决策
            'success': False,
            'error': str(e),
            'is_demo': False,
            'error_reason': f"分析失败: {str(e)}"
        }

def format_analysis_results(results):
    """格式化分析结果用于显示"""
    
    if not results['success']:
        return {
            'error': results['error'],
            'success': False
        }
    
    state = results['state']
    decision = results['decision']

    # 提取关键信息
    # decision 可能是字符串（如 "BUY", "SELL", "HOLD"）或字典
    if isinstance(decision, str):
        # 将英文投资建议转换为中文
        action_translation = {
            'BUY': '买入',
            'SELL': '卖出',
            'HOLD': '持有',
            'buy': '买入',
            'sell': '卖出',
            'hold': '持有'
        }
        action = action_translation.get(decision.strip(), decision.strip())

        formatted_decision = {
            'action': action,
            'confidence': 0.7,  # 默认置信度
            'risk_score': 0.3,  # 默认风险分数
            'target_price': None,  # 字符串格式没有目标价格
            'reasoning': f'基于AI分析，建议{decision.strip().upper()}'
        }
    elif isinstance(decision, dict):
        # 处理目标价格 - 确保正确提取数值
        target_price = decision.get('target_price')
        if target_price is not None and target_price != 'N/A':
            try:
                # 尝试转换为浮点数
                if isinstance(target_price, str):
                    # 移除货币符号和空格
                    clean_price = target_price.replace('$', '').replace('¥', '').replace('￥', '').strip()
                    target_price = float(clean_price) if clean_price and clean_price != 'None' else None
                elif isinstance(target_price, (int, float)):
                    target_price = float(target_price)
                else:
                    target_price = None
            except (ValueError, TypeError):
                target_price = None
        else:
            target_price = None

        # 将英文投资建议转换为中文
        action_translation = {
            'BUY': '买入',
            'SELL': '卖出',
            'HOLD': '持有',
            'buy': '买入',
            'sell': '卖出',
            'hold': '持有'
        }
        action = decision.get('action', '持有')
        chinese_action = action_translation.get(action, action)

        formatted_decision = {
            'action': chinese_action,
            'confidence': decision.get('confidence', 0.5),
            'risk_score': decision.get('risk_score', 0.3),
            'target_price': target_price,
            'reasoning': decision.get('reasoning', '暂无分析推理')
        }
    else:
        # 处理其他类型
        formatted_decision = {
            'action': '持有',
            'confidence': 0.5,
            'risk_score': 0.3,
            'target_price': None,
            'reasoning': f'分析结果: {str(decision)}'
        }
    
    # 格式化状态信息
    formatted_state = {}
    
    # 处理各个分析模块的结果 - 包含完整的智能体团队分析
    analysis_keys = [
        'market_report',
        'fundamentals_report',
        'sentiment_report',
        'news_report',
        'risk_assessment',
        'investment_plan',
        # 添加缺失的团队决策数据，确保与CLI端一致
        'investment_debate_state',  # 研究团队辩论（多头/空头研究员）
        'trader_investment_plan',   # 交易团队计划
        'risk_debate_state',        # 风险管理团队决策
        'final_trade_decision'      # 最终交易决策
    ]
    
    for key in analysis_keys:
        if key in state:
            # 对文本内容进行中文化处理
            content = state[key]
            if isinstance(content, str):
                content = translate_analyst_labels(content)
            formatted_state[key] = content
        elif key == 'risk_assessment':
            # 特殊处理：从 risk_debate_state 生成 risk_assessment
            risk_assessment = extract_risk_assessment(state)
            if risk_assessment:
                formatted_state[key] = risk_assessment
    
    return {
        'stock_symbol': results['stock_symbol'],
        'decision': formatted_decision,
        'state': formatted_state,
        'success': True,
        # 将配置信息放在顶层，供前端直接访问
        'analysis_date': results['analysis_date'],
        'analysts': results['analysts'],
        'research_depth': results['research_depth'],
        'llm_provider': results.get('llm_provider', 'dashscope'),
        'llm_model': results['llm_model'],
        'metadata': {
            'analysis_date': results['analysis_date'],
            'analysts': results['analysts'],
            'research_depth': results['research_depth'],
            'llm_provider': results.get('llm_provider', 'dashscope'),
            'llm_model': results['llm_model']
        }
    }

def validate_analysis_params(stock_symbol, analysis_date, analysts, research_depth, market_type="美股"):
    """验证分析参数"""

    errors = []

    # 验证股票代码
    if not stock_symbol or len(stock_symbol.strip()) == 0:
        errors.append("股票代码不能为空")
    elif len(stock_symbol.strip()) > 10:
        errors.append("股票代码长度不能超过10个字符")
    else:
        # 根据市场类型验证代码格式
        symbol = stock_symbol.strip()
        if market_type == "A股":
            # A股：6位数字
            import re
            if not re.match(r'^\d{6}$', symbol):
                errors.append("A股代码格式错误，应为6位数字（如：000001）")
        elif market_type == "港股":
            # 港股：4-5位数字.HK 或 纯4-5位数字
            import re
            symbol_upper = symbol.upper()
            # 检查是否为 XXXX.HK 或 XXXXX.HK 格式
            hk_format = re.match(r'^\d{4,5}\.HK$', symbol_upper)
            # 检查是否为纯4-5位数字格式
            digit_format = re.match(r'^\d{4,5}$', symbol)

            if not (hk_format or digit_format):
                errors.append("港股代码格式错误，应为4位数字.HK（如：0700.HK）或4位数字（如：0700）")
        elif market_type == "美股":
            # 美股：1-5位字母
            import re
            if not re.match(r'^[A-Z]{1,5}$', symbol.upper()):
                errors.append("美股代码格式错误，应为1-5位字母（如：AAPL）")
    
    # 验证分析师列表
    if not analysts or len(analysts) == 0:
        errors.append("必须至少选择一个分析师")
    
    valid_analysts = ['market', 'social', 'news', 'fundamentals']
    invalid_analysts = [a for a in analysts if a not in valid_analysts]
    if invalid_analysts:
        errors.append(f"无效的分析师类型: {', '.join(invalid_analysts)}")
    
    # 验证研究深度
    if not isinstance(research_depth, int) or research_depth < 1 or research_depth > 4:
        errors.append("研究深度必须是1-4之间的整数")
    
    # 验证分析日期
    try:
        from datetime import datetime
        datetime.strptime(analysis_date, '%Y-%m-%d')
    except ValueError:
        errors.append("分析日期格式无效，应为YYYY-MM-DD格式")
    
    return len(errors) == 0, errors

def get_supported_stocks():
    """获取支持的股票列表"""
    
    # 常见的美股股票代码
    popular_stocks = [
        {'symbol': 'AAPL', 'name': '苹果公司', 'sector': '科技'},
        {'symbol': 'MSFT', 'name': '微软', 'sector': '科技'},
        {'symbol': 'GOOGL', 'name': '谷歌', 'sector': '科技'},
        {'symbol': 'AMZN', 'name': '亚马逊', 'sector': '消费'},
        {'symbol': 'TSLA', 'name': '特斯拉', 'sector': '汽车'},
        {'symbol': 'NVDA', 'name': '英伟达', 'sector': '科技'},
        {'symbol': 'META', 'name': 'Meta', 'sector': '科技'},
        {'symbol': 'NFLX', 'name': '奈飞', 'sector': '媒体'},
        {'symbol': 'AMD', 'name': 'AMD', 'sector': '科技'},
        {'symbol': 'INTC', 'name': '英特尔', 'sector': '科技'},
        {'symbol': 'SPY', 'name': 'S&P 500 ETF', 'sector': 'ETF'},
        {'symbol': 'QQQ', 'name': '纳斯达克100 ETF', 'sector': 'ETF'},
    ]
    
    return popular_stocks

