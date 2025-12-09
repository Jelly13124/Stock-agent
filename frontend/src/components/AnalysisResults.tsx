import { useState, useEffect } from 'react'
import type { AnalysisResult } from '../lib/api'
import { PriceChart } from './PriceChart'
import { fetchStockData } from '../lib/finnhub'
import './AnalysisResults.css'

interface AnalysisResultsProps {
  result: AnalysisResult
  onNewAnalysis: () => void
  uiLanguage: 'Chinese' | 'English'
}

type TabKey = 'overview' | 'market' | 'fundamentals' | 'news' | 'risk' | 'investment_plan' | 'trader_plan' | 'risk_debate' | 'final_decision'

const translations = {
  Chinese: {
    analysisReport: '分析报告',
    newAnalysis: '发起新分析',
    investmentDecision: '投资决策',
    marketAnalysis: '市场分析',
    fundamentals: '基本面',
    news: '新闻',
    riskAssessment: '风险评估',
    researchTeam: '研究团队决策',
    traderPlan: '交易团队计划',
    riskTeam: '风险管理团队',
    finalDecision: '最终交易决策',
    targetPrice: '目标价',
    confidence: '置信度',
    riskScore: '风险评分',
    decisionReasoning: '决策理由',
    loadingChart: '正在加载市场数据...',
    noChartData: '暂无历史价格数据可供展示',
    chartError: '请检查股票代码是否正确，或确认Finnhub API密钥配置',
    failed: '分析失败',
    unavailable: '分析结果不可用',
    unknownError: '未知错误',
    chartTitle: '30天历史价格走势 (Finnhub实时数据)',
    marketTechAnalysis: '市场技术分析',
    fundamentalsAnalysis: '基本面分析',
    newsAnalysis: '新闻分析',
    riskAnalysis: '风险评估',
    researchTeamDecision: '研究团队决策',
    traderTeamPlan: '交易团队计划',
    riskMgmtTeam: '风险管理团队决策',
    finalTradeDecision: '最终交易决策',
  },
  English: {
    analysisReport: 'Analysis Report',
    newAnalysis: 'New Analysis',
    investmentDecision: 'Investment Decision',
    marketAnalysis: 'Market Analysis',
    fundamentals: 'Fundamentals',
    news: 'News',
    riskAssessment: 'Risk Assessment',
    researchTeam: 'Research Team Decision',
    traderPlan: 'Trader Team Plan',
    riskTeam: 'Risk Mgmt Team',
    finalDecision: 'Final Trade Decision',
    targetPrice: 'Target Price',
    confidence: 'Confidence',
    riskScore: 'Risk Score',
    decisionReasoning: 'Decision Reasoning',
    loadingChart: 'Loading market data...',
    noChartData: 'No historical price data available',
    chartError: 'Check stock symbol or Finnhub API key configuration',
    failed: 'Analysis Failed',
    unavailable: 'Analysis Result Unavailable',
    unknownError: 'Unknown Error',
    chartTitle: '30-Day Price History (Finnhub Real-time)',
    marketTechAnalysis: 'Market Technical Analysis',
    fundamentalsAnalysis: 'Fundamental Analysis',
    newsAnalysis: 'News Analysis',
    riskAnalysis: 'Risk Assessment',
    researchTeamDecision: 'Research Team Decision',
    traderTeamPlan: 'Trader Team Plan',
    riskMgmtTeam: 'Risk Management Team Decision',
    finalTradeDecision: 'Final Trade Decision',
  }
}

// Helper to format report text with markdown-like styling
function FormattedReport({ text }: { text: string }) {
  return (
    <div className="report-formatted">
      {text.split('\n').map((line, idx) => {
        if (!line.trim()) return <br key={idx} />
        
        // Headers (##, ###)
        if (line.startsWith('###')) {
          return <h4 key={idx} className="report-h4">{line.replace(/^###\s*/, '')}</h4>
        }
        if (line.startsWith('##')) {
          return <h3 key={idx} className="report-h3">{line.replace(/^##\s*/, '')}</h3>
        }
        
        // Bullet points
        if (line.trim().startsWith('-') || line.trim().startsWith('*')) {
          return <li key={idx} className="report-li">{line.replace(/^[\s-*]+/, '')}</li>
        }
        
        // Numbered lists
        if (/^\d+\./.test(line.trim())) {
          return <li key={idx} className="report-li numbered">{line.replace(/^\d+\.\s*/, '')}</li>
        }
        
        // Bold text (**text**)
        const boldText = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        
        // Regular paragraph
        return <p key={idx} className="report-p" dangerouslySetInnerHTML={{ __html: boldText }} />
      })}
    </div>
  )
}

export function AnalysisResults({ result, onNewAnalysis, uiLanguage }: AnalysisResultsProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview')
  const [marketChartData, setMarketChartData] = useState<Array<{ date: string; price: number; volume?: number }>>([])
  const [isLoadingChart, setIsLoadingChart] = useState(false)
  const t = translations[uiLanguage]

  // Fetch real market data from Finnhub when component mounts
  useEffect(() => {
    const loadMarketData = async () => {
      if (!result.symbol) return
      
      setIsLoadingChart(true)
      try {
        const data = await fetchStockData(result.symbol, 30)
        setMarketChartData(data)
      } catch (error) {
        console.error('Failed to load market data:', error)
        setMarketChartData([])
      } finally {
        setIsLoadingChart(false)
      }
    }

    loadMarketData()
  }, [result.symbol])

  if (!result.result) {
    return (
      <div className="results-container">
        <div className="result-banner error">{t.unavailable}</div>
      </div>
    )
  }

  const { result: data } = result

  if (!data.success) {
    return (
      <div className="results-container">
        <div className="result-banner error">
          <h3>❌ {t.failed}</h3>
          <p>{data.error || t.unknownError}</p>
        </div>
        <button onClick={onNewAnalysis} className="new-analysis-btn">
          {t.newAnalysis}
        </button>
      </div>
    )
  }

  const getActionColor = (action?: string) => {
    if (!action) return 'neutral'
    const normalized = action.toLowerCase()
    if (normalized.includes('买') || normalized === 'buy') return 'buy'
    if (normalized.includes('卖') || normalized === 'sell') return 'sell'
    return 'hold'
  }

  const actionColor = getActionColor(data.action)

  const tabs = [
    { key: 'overview' as TabKey, label: `📊 ${t.investmentDecision}`, icon: '📊' },
    { key: 'market' as TabKey, label: `📈 ${t.marketAnalysis}`, icon: '📈', hasData: !!data.market_report },
    { key: 'fundamentals' as TabKey, label: `💰 ${t.fundamentals}`, icon: '💰', hasData: !!data.fundamentals_report },
    { key: 'news' as TabKey, label: `📰 ${t.news}`, icon: '📰', hasData: !!data.news_report },
    { key: 'risk' as TabKey, label: `⚠️ ${t.riskAssessment}`, icon: '⚠️', hasData: !!data.risk_assessment },
    { key: 'investment_plan' as TabKey, label: `🔎 ${t.researchTeam}`, icon: '🔎', hasData: !!data.investment_debate_state },
    { key: 'trader_plan' as TabKey, label: `💼 ${t.traderPlan}`, icon: '💼', hasData: !!data.trader_investment_plan },
    { key: 'risk_debate' as TabKey, label: `🔥 ${t.riskTeam}`, icon: '🔥', hasData: !!data.risk_debate_state },
    { key: 'final_decision' as TabKey, label: `🎯 ${t.finalDecision}`, icon: '🎯', hasData: !!data.final_trade_decision },
  ]

  return (
    <div className="results-container">
      <div className="results-header">
        <div className="header-left">
          <h2>📊 {t.analysisReport}</h2>
          <div className="stock-info-inline">
            <span className="info-badge">{result.symbol}</span>
            <span className="info-badge">{result.market}</span>
            <span className="info-badge">
              {result.completed_at
                ? new Date(result.completed_at).toLocaleTimeString(uiLanguage === 'Chinese' ? 'zh-CN' : 'en-US')
                : ''}
            </span>
          </div>
        </div>
        <button onClick={onNewAnalysis} className="new-analysis-btn">
          {t.newAnalysis}
        </button>
      </div>

      {/* Tab Navigation */}
      <nav className="tab-nav">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? 'active' : ''} ${
              tab.hasData === false ? 'disabled' : ''
            }`}
            onClick={() => tab.hasData !== false && setActiveTab(tab.key)}
            disabled={tab.hasData === false}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label.replace(/^[📊📈💰📰💬⚠️]\s/, '')}</span>
          </button>
        ))}
      </nav>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="tab-pane">
            <div className={`decision-card ${actionColor}`}>
              <h3>🎯 {t.investmentDecision}</h3>
              <div className="decision-main">
                <div className="decision-action">{data.action || 'N/A'}</div>
                <div className="decision-details">
                  {data.target_price && (
                    <div className="detail-item">
                      <span className="detail-label">{t.targetPrice}：</span>
                      <span className="detail-value">
                        {typeof data.target_price === 'number'
                          ? `$${data.target_price.toFixed(2)}`
                          : data.target_price}
                      </span>
                    </div>
                  )}
                  {data.confidence !== undefined && (
                    <div className="detail-item">
                      <span className="detail-label">{t.confidence}：</span>
                      <span className="detail-value">{(data.confidence * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {data.risk_score !== undefined && (
                    <div className="detail-item">
                      <span className="detail-label">{t.riskScore}：</span>
                      <span className="detail-value">{(data.risk_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              </div>
              {data.reasoning && (
                <div className="decision-reasoning">
                  <strong>{t.decisionReasoning}：</strong>
                  <FormattedReport text={data.reasoning} />
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'market' && data.market_report && (
          <div className="tab-pane">
            {isLoadingChart ? (
              <div className="chart-empty">
                <p>📊 {t.loadingChart}</p>
              </div>
            ) : marketChartData.length > 0 ? (
              <PriceChart
                data={marketChartData}
                title={`${result.symbol} ${t.chartTitle}`}
              />
            ) : (
              <div className="chart-empty">
                <p>📊 {t.noChartData}</p>
                <p style={{ fontSize: '0.85rem', color: '#5a7a96', marginTop: '0.5rem' }}>
                  {t.chartError}
                </p>
              </div>
            )}
            <div className="report-section">
              <h3>📈 {t.marketTechAnalysis}</h3>
              <div className="report-content">
                <FormattedReport text={data.market_report} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'fundamentals' && data.fundamentals_report && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>💰 {t.fundamentalsAnalysis}</h3>
              <div className="report-content">
                <FormattedReport text={data.fundamentals_report} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'news' && data.news_report && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>📰 {t.newsAnalysis}</h3>
              <div className="report-content">
                <FormattedReport text={data.news_report} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risk' && data.risk_assessment && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>⚠️ {t.riskAnalysis}</h3>
              <div className="report-content">
                <FormattedReport text={data.risk_assessment} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'investment_plan' && data.investment_debate_state && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>🔎 {t.researchTeamDecision}</h3>
              <div className="report-content">
                <FormattedReport text={data.investment_debate_state} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trader_plan' && data.trader_investment_plan && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>💼 {t.traderTeamPlan}</h3>
              <div className="report-content">
                <FormattedReport text={data.trader_investment_plan} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risk_debate' && data.risk_debate_state && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>🔥 {t.riskMgmtTeam}</h3>
              <div className="report-content">
                <FormattedReport text={data.risk_debate_state} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'final_decision' && data.final_trade_decision && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>🎯 {t.finalTradeDecision}</h3>
              <div className="report-content">
                <FormattedReport text={data.final_trade_decision} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
