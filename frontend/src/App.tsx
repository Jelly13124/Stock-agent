import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import { createAnalysis, getAnalysisStatus, getAnalysisResult } from './lib/api'
import type { AnalysisResult, AnalysisStatus } from './lib/api'
import { AnalysisResults } from './components/AnalysisResults'

const defaultForm = {
  symbol: '',
  market: '美股',
  researchDepth: 1,
  llmProvider: 'google',
  includeRisk: true,
  includeSentiment: true,
  includeNews: true,
  analysisDate: new Date().toISOString().split('T')[0], // YYYY-MM-DD format
}

type Language = 'Chinese' | 'English'

const translations = {
  Chinese: {
    title: 'AI 股票分析助手',
    startAnalysis: '发起新的股票分析',
    symbol: '股票代码',
    market: '市场',
    analysisDate: '分析日期',
    researchDepth: '研究深度',
    llmProvider: 'LLM 提供商',
    includeRisk: '包含风险评估（多角度风险分析）',
    includeSentiment: '包含市场情绪评估（Social Analysis）',
    includeNews: '包含新闻分析（News Analysis）',
    submit: '提交分析请求',
    submitting: '分析中...',
    status: '状态',
    startedAt: '开始时间',
    queued: '排队中',
    running: '分析中',
    failed: '失败',
    completed: '完成',
    depthOptions: {
      1: '1级 (2-4分钟): 快速概览，基础技术指标',
      2: '2级 (4-6分钟): 标准分析，技术+基本面',
      3: '3级 (6-10分钟): 深度分析，推荐',
      4: '4级 (10-15分钟): 全面分析，多轮智能体辩论',
    },
    marketOptions: {
      '美股': '美股',
      'A股': 'A股',
      '港股': '港股',
    },
    language: '语言 (Language)'
  },
  English: {
    title: 'AI Stock Analysis Assistant',
    startAnalysis: 'Start New Stock Analysis',
    symbol: 'Stock Symbol',
    market: 'Market',
    analysisDate: 'Analysis Date',
    researchDepth: 'Research Depth',
    llmProvider: 'LLM Provider',
    includeRisk: 'Include Risk Assessment (Multi-angle Risk Analysis)',
    includeSentiment: 'Include Sentiment Analysis (Social Analysis)',
    includeNews: 'Include News Analysis',
    submit: 'Submit Analysis Request',
    submitting: 'Analyzing...',
    status: 'Status',
    startedAt: 'Started At',
    queued: 'Queued',
    running: 'Running',
    failed: 'Failed',
    completed: 'Completed',
    depthOptions: {
      1: 'Level 1 (2-4 min): Quick Overview, Basic Technicals',
      2: 'Level 2 (4-6 min): Standard Analysis, Technical + Fundamental',
      3: 'Level 3 (6-10 min): Deep Analysis, Recommendation',
      4: 'Level 4 (10-15 min): Comprehensive, Multi-Round Debate',
    },
    marketOptions: {
      '美股': 'US Market',
      'A股': 'A-Share',
      '港股': 'HK Market',
    },
    language: 'Language (语言)'
  }
}

function App() {
  const [form, setForm] = useState(defaultForm)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uiLanguage, setUiLanguage] = useState<Language>('Chinese')

  const t = translations[uiLanguage]

  // Poll for analysis status
  useEffect(() => {
    if (!analysisId) return

    let isCancelled = false
    const pollInterval = 2000 // Poll every 2 seconds

    const poll = async () => {
      try {
        const status = await getAnalysisStatus(analysisId)
        if (isCancelled) return

        setAnalysisStatus(status)

        if (status.status === 'completed') {
          // Fetch full result
          const result = await getAnalysisResult(analysisId)
          if (!isCancelled) {
            setAnalysisResult(result)
            setIsSubmitting(false)
          }
        } else if (status.status === 'failed') {
          setError(status.error || t.failed)
          setIsSubmitting(false)
        } else {
          // Continue polling
          setTimeout(poll, pollInterval)
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : '获取状态失败')
          setIsSubmitting(false)
        }
      }
    }

    poll()

    return () => {
      isCancelled = true
    }
  }, [analysisId, t.failed])

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = event.target
    const checked = type === 'checkbox' ? (event.target as HTMLInputElement).checked : undefined
    
    // Capitalize stock symbol input
    const finalValue = name === 'symbol' ? value.toUpperCase() : value
    
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : name === 'researchDepth' ? Number(finalValue) : finalValue,
    }))
  }

  const handleLanguageChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setUiLanguage(event.target.value as Language)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setAnalysisId(null)
    setAnalysisStatus(null)
    setAnalysisResult(null)

    try {
      // Build analysts array based on selections
      const analysts = ['market', 'fundamentals'] // Core analysts
      
      if (form.includeNews) {
        analysts.push('news')
      }

      if (form.includeSentiment) {
        analysts.push('social')
      }
      
      const response = await createAnalysis({
        symbol: form.symbol,
        market: form.market,
        research_depth: form.researchDepth,
        llm_provider: form.llmProvider,
        analysts,
        analysis_date: form.analysisDate,
        include_risk_assessment: form.includeRisk,
      })
      setAnalysisId(response.analysis_id)
      // isSubmitting will be set to false by polling effect when complete
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Unknown submission error')
      }
      setIsSubmitting(false)
    }
  }

  const handleNewAnalysis = () => {
    setAnalysisId(null)
    setAnalysisStatus(null)
    setAnalysisResult(null)
    setError(null)
    setForm(defaultForm)
  }

  // Show results if available
  if (analysisResult) {
    return (
      <div className="app-container">
        <header className="app-header">
          <div className="header-content">
            <h1>{t.title}</h1>
            <div className="language-selector">
              <select value={uiLanguage} onChange={handleLanguageChange}>
                <option value="Chinese">中文 (Chinese)</option>
                <option value="English">English</option>
              </select>
            </div>
          </div>
        </header>
        <main>
          <AnalysisResults 
            result={analysisResult} 
            onNewAnalysis={handleNewAnalysis} 
            uiLanguage={uiLanguage}
          />
        </main>
      </div>
    )
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <h1>{t.title}</h1>
          <div className="language-selector">
            <select value={uiLanguage} onChange={handleLanguageChange}>
              <option value="Chinese">中文 (Chinese)</option>
              <option value="English">English</option>
            </select>
          </div>
        </div>
      </header>

      <main>
        <section className="card">
          <h2>{t.startAnalysis}</h2>
          <form onSubmit={handleSubmit} className="analysis-form">
            <label>
              {t.symbol}
              <input
                name="symbol"
                value={form.symbol}
                onChange={handleChange}
                placeholder="例如：AAPL"
                required
                disabled={isSubmitting}
              />
            </label>

            <label>
              {t.market}
              <select name="market" value={form.market} onChange={handleChange} disabled={isSubmitting}>
                <option value="美股">{t.marketOptions['美股']}</option>
                <option value={1}>{t.marketOptions['A股']}</option>
                <option value={2}>{t.marketOptions['港股']}</option>
              </select>
            </label>

            <label>
              {t.analysisDate}
              <input
                type="date"
                name="analysisDate"
                value={form.analysisDate}
                onChange={handleChange}
                disabled={isSubmitting}
                max={new Date().toISOString().split('T')[0]}
              />
            </label>

            <label>
              {t.researchDepth}
              <select name="researchDepth" value={form.researchDepth} onChange={handleChange} disabled={isSubmitting}>
                <option value={1}>{t.depthOptions[1]}</option>
                <option value={2}>{t.depthOptions[2]}</option>
                <option value={3}>{t.depthOptions[3]}</option>
                <option value={4}>{t.depthOptions[4]}</option>
              </select>
            </label>

            <label>
              {t.llmProvider}
              <select name="llmProvider" value={form.llmProvider} onChange={handleChange} disabled={isSubmitting}>
                <option value="google">Google Gemini</option>
                <option value="dashscope">阿里百炼</option>
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI</option>
              </select>
            </label>

            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="includeRisk"
                  checked={form.includeRisk}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                <span>{t.includeRisk}</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="includeSentiment"
                  checked={form.includeSentiment}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                <span>{t.includeSentiment}</span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="includeNews"
                  checked={form.includeNews}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                <span>{t.includeNews}</span>
              </label>
            </div>

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t.submitting : t.submit}
            </button>
          </form>

          {analysisStatus && (
            <div className="result-banner success">
              <strong>{t.status}：{t[analysisStatus.status] || analysisStatus.status}</strong>
              <br />
              {t.symbol}：{analysisStatus.symbol} ({analysisStatus.market})
              {analysisStatus.started_at && (
                <>
                  <br />
                  {t.startedAt}：{new Date(analysisStatus.started_at).toLocaleString(uiLanguage === 'Chinese' ? 'zh-CN' : 'en-US')}
                </>
              )}
            </div>
          )}

          {error && <div className="result-banner error">{error}</div>}
        </section>
      </main>
    </div>
  )
}

export default App
