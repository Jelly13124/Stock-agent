import { useState, useEffect } from 'react'
import type { AnalysisResult } from '../lib/api'
import { PriceChart } from './PriceChart'
import { fetchStockData } from '../lib/finnhub'
import './AnalysisResults.css'

interface AnalysisResultsProps {
  result: AnalysisResult
  onNewAnalysis: () => void
}

type TabKey = 'overview' | 'market' | 'fundamentals' | 'news' | 'risk' | 'investment_plan' | 'trader_plan' | 'risk_debate' | 'final_decision'

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

// Helper to convert market data to chart format
function convertMarketDataToChartFormat(marketData: Array<{
  date: string
  open?: number
  high?: number
  low?: number
  close: number
  volume?: number
}>) {
  return marketData.map(d => ({
    date: d.date,
    price: d.close, // Use closing price for the chart
    volume: d.volume
  }))
}

export function AnalysisResults({ result, onNewAnalysis }: AnalysisResultsProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview')
  const [marketChartData, setMarketChartData] = useState<Array<{ date: string; price: number; volume?: number }>>([])
  const [isLoadingChart, setIsLoadingChart] = useState(false)

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
        <div className="result-banner error">分析结果不可用</div>
      </div>
    )
  }

  const { result: data } = result

  if (!data.success) {
    return (
      <div className="results-container">
        <div className="result-banner error">
          <h3>❌ 分析失败</h3>
          <p>{data.error || '未知错误'}</p>
        </div>
        <button onClick={onNewAnalysis} className="new-analysis-btn">
          发起新分析
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
    { key: 'overview' as TabKey, label: '📊 投资决策', icon: '📊' },
    { key: 'market' as TabKey, label: '📈 市场分析', icon: '📈', hasData: !!data.market_report },
    { key: 'fundamentals' as TabKey, label: '💰 基本面', icon: '💰', hasData: !!data.fundamentals_report },
    { key: 'news' as TabKey, label: '📰 新闻', icon: '📰', hasData: !!data.news_report },
    { key: 'risk' as TabKey, label: '⚠️ 风险评估', icon: '⚠️', hasData: !!data.risk_assessment },
    { key: 'investment_plan' as TabKey, label: '🔎 研究团队决策', icon: '🔎', hasData: !!data.investment_debate_state },
    { key: 'trader_plan' as TabKey, label: '💼 交易团队计划', icon: '💼', hasData: !!data.trader_investment_plan },
    { key: 'risk_debate' as TabKey, label: '🔥 风险管理团队', icon: '🔥', hasData: !!data.risk_debate_state },
    { key: 'final_decision' as TabKey, label: '🎯 最终交易决策', icon: '🎯', hasData: !!data.final_trade_decision },
  ]

  return (
    <div className="results-container">
      <div className="results-header">
        <div className="header-left">
          <h2>📊 分析报告</h2>
          <div className="stock-info-inline">
            <span className="info-badge">{result.symbol}</span>
            <span className="info-badge">{result.market}</span>
            <span className="info-badge">
              {result.completed_at
                ? new Date(result.completed_at).toLocaleTimeString('zh-CN')
                : ''}
            </span>
          </div>
        </div>
        <button onClick={onNewAnalysis} className="new-analysis-btn">
          发起新分析
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
              <h3>🎯 投资决策</h3>
              <div className="decision-main">
                <div className="decision-action">{data.action || 'N/A'}</div>
                <div className="decision-details">
                  {data.target_price && (
                    <div className="detail-item">
                      <span className="detail-label">目标价：</span>
                      <span className="detail-value">
                        {typeof data.target_price === 'number'
                          ? `$${data.target_price.toFixed(2)}`
                          : data.target_price}
                      </span>
                    </div>
                  )}
                  {data.confidence !== undefined && (
                    <div className="detail-item">
                      <span className="detail-label">置信度：</span>
                      <span className="detail-value">{(data.confidence * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {data.risk_score !== undefined && (
                    <div className="detail-item">
                      <span className="detail-label">风险评分：</span>
                      <span className="detail-value">{(data.risk_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              </div>
              {data.reasoning && (
                <div className="decision-reasoning">
                  <strong>决策理由：</strong>
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
                <p>📊 正在加载市场数据...</p>
              </div>
            ) : marketChartData.length > 0 ? (
              <PriceChart
                data={marketChartData}
                title={`${result.symbol} 30天历史价格走势 (Finnhub实时数据)`}
              />
            ) : (
              <div className="chart-empty">
                <p>📊 暂无历史价格数据可供展示</p>
                <p style={{ fontSize: '0.85rem', color: '#5a7a96', marginTop: '0.5rem' }}>
                  请检查股票代码是否正确，或确认Finnhub API密钥配置
                </p>
              </div>
            )}
            <div className="report-section">
              <h3>📈 市场技术分析</h3>
              <div className="report-content">
                <FormattedReport text={data.market_report} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'fundamentals' && data.fundamentals_report && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>💰 基本面分析</h3>
              <div className="report-content">
                <FormattedReport text={data.fundamentals_report} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'news' && data.news_report && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>📰 新闻分析</h3>
              <div className="report-content">
                <FormattedReport text={data.news_report} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risk' && data.risk_assessment && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>⚠️ 风险评估</h3>
              <div className="report-content">
                <FormattedReport text={data.risk_assessment} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'investment_plan' && data.investment_debate_state && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>🔎 研究团队决策</h3>
              <div className="report-content">
                <FormattedReport text={data.investment_debate_state} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trader_plan' && data.trader_investment_plan && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>💼 交易团队计划</h3>
              <div className="report-content">
                <FormattedReport text={data.trader_investment_plan} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risk_debate' && data.risk_debate_state && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>🔥 风险管理团队决策</h3>
              <div className="report-content">
                <FormattedReport text={data.risk_debate_state} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'final_decision' && data.final_trade_decision && (
          <div className="tab-pane">
            <div className="report-section">
              <h3>🎯 最终交易决策</h3>
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

