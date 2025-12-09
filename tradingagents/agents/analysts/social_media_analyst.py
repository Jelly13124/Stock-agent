from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from datetime import datetime

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

logger = get_logger("analysts.social")


def create_social_media_analyst(llm, toolkit):
    @log_analyst_module("social_media")
    def social_media_analyst_node(state):
        start_time = datetime.now()
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        logger.info(f"[社媒分析师] 开始分析 {ticker} 的社媒舆情，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[社媒分析师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 准备工具列表
        tools = []
        
        # 尝试添加 Reddit 工具
        if hasattr(toolkit, 'get_reddit_company_news'):
            tools.append(toolkit.get_reddit_company_news)
            logger.info(f"[社媒分析师] 已加载工具: get_reddit_company_news")
        
        # 如果没有专门的社媒工具，可能会回退到新闻工具或搜索工具
        # 这里我们假设至少有 Reddit 工具或通用搜索工具
        if not tools and hasattr(toolkit, 'get_google_news'):
             tools.append(toolkit.get_google_news) # 回退方案
             logger.info(f"[社媒分析师] 未找到专用社媒工具，回退使用: get_google_news")

        # 检查历史消息中是否已经包含工具调用结果
        has_tool_output = False
        from langchain_core.messages import ToolMessage
        for msg in state.get("messages", []):
            if isinstance(msg, ToolMessage):
                has_tool_output = True
                break

        # 根据状态动态调整系统提示
        if has_tool_output:
            logger.info(f"[社媒分析师] 检测到已有工具输出，切换为分析模式")
            system_message = (
                """您是一位专业的社交媒体舆情分析师。数据已获取成功。
                请基于上述工具获取的社交媒体数据，撰写详细的舆情分析报告。

                分析要点：
                1. 情绪极性：正面 vs 负面讨论的比例
                2. 讨论热度：帖子数量和互动量的变化趋势
                3. 关键话题：投资者最关注的具体问题
                4. 舆情影响评估：对股价的潜在推动力

                请直接输出分析报告，包含具体的观点引用和数据支持。"""
            )
        else:
            system_message = (
                """您是一位专业的社交媒体舆情分析师，负责分析散户投资者和市场参与者在社交平台上的讨论情绪。

                🚨 关键要求：
                1. 您必须立即调用工具获取社交媒体数据（如Reddit讨论）。
                2. 不要凭空捏造数据，必须基于工具返回的真实内容。
                3. 必须调用工具！不要说"我将要调用"，直接调用。

                您可以访问以下工具：{tool_names}。
                
                当前日期是{current_date}。我们正在分析公司{ticker}。
                请用中文回答。"""
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_message
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        
        # 获取模型信息
        model_info = ""
        try:
            if hasattr(llm, 'model_name'):
                model_info = f"{llm.__class__.__name__}:{llm.model_name}"
            else:
                model_info = llm.__class__.__name__
        except:
            model_info = "Unknown"
        
        logger.info(f"[社媒分析师] 准备调用LLM进行舆情分析，模型: {model_info}")

        # 使用统一的Google工具调用处理器
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        
        try:
            result = chain.invoke(state["messages"])
        except Exception as e:
            logger.error(f"[社媒分析师] LLM调用失败: {e}")
            # 返回空报告以避免崩溃
            from langchain_core.messages import AIMessage
            return {
                "messages": [AIMessage(content="由于技术原因，暂时无法获取社交媒体分析报告。")],
                "sentiment_report": "由于技术原因，暂时无法获取社交媒体分析报告。",
            }
            
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[社媒分析师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [社媒分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=ticker, # 社媒分析通常直接用代码或简称
                analyst_type="社媒舆情分析",
                specific_requirements="重点关注散户情绪、讨论热度、潜在的市场非理性行为。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="社媒分析师"
            )
            
            # 注意：这里我们返回 sentiment_report 键，对应 graph 中的状态定义
            return {
                "messages": messages,
                "sentiment_report": report,
            }
        else:
            # 非Google模型的标准处理
            logger.info(f"[社媒分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            
            # 检查是否有工具调用
            if hasattr(result, 'tool_calls') and result.tool_calls:
                logger.info(f"[社媒分析师] LLM请求调用工具: {len(result.tool_calls)} 个")
                # 返回包含工具调用的原始消息，让Graph路由到工具执行节点
                return {
                    "messages": [result],
                    # 这里不更新sentiment_report，因为分析还没完成
                }

            # 如果没有工具调用，说明是最终分析报告
            report = result.content
            logger.info(f"[社媒分析师] 生成分析报告，长度: {len(report)}")
            
            return {
                "messages": [result],
                "sentiment_report": report,
            }

    return social_media_analyst_node

