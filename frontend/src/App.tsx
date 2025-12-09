import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import { createAnalysis, getHealth, getAnalysisStatus, getAnalysisResult } from './lib/api'
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

function App() {
  const [health, setHealth] = useState<string>('Checking backend...')
  const [form, setForm] = useState(defaultForm)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getHealth()
      .then((response) => setHealth(`✅ Backend ready (${response.service})`))
      .catch((err) => setHealth(`⚠️ Backend unavailable: ${err.message}`))
  }, [])

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
          setError(status.error || '分析失败')
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
  }, [analysisId])

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
          <h1 style={{ textAlign: 'center', width: '100%' }}>AI 股票分析助手</h1>
        </header>
        <main>
          <AnalysisResults result={analysisResult} onNewAnalysis={handleNewAnalysis} />
        </main>
      </div>
    )
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 style={{ textAlign: 'center', width: '100%' }}>AI 股票分析助手</h1>
      </header>

      <main>
        <section className="card">
          <h2>发起新的股票分析</h2>
          <form onSubmit={handleSubmit} className="analysis-form">
            <label>
              股票代码
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
              市场
              <select name="market" value={form.market} onChange={handleChange} disabled={isSubmitting}>
                <option value="美股">美股</option>
                <option value="A股">A股</option>
                <option value="港股">港股</option>
              </select>
            </label>

            <label>
              分析日期
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
              研究深度
              <select name="researchDepth" value={form.researchDepth} onChange={handleChange} disabled={isSubmitting}>
                <option value={1}>1级 (2-4分钟): 快速概览，基础技术指标</option>
                <option value={2}>2级 (4-6分钟): 标准分析，技术+基本面</option>
                <option value={3}>3级 (6-10分钟): 深度分析，推荐</option>
                <option value={4}>4级 (10-15分钟): 全面分析，多轮智能体辩论</option>
              </select>
            </label>

            <label>
              LLM 提供商
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
                <span>包含风险评估（多角度风险分析）</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="includeSentiment"
                  checked={form.includeSentiment}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                <span>包含市场情绪评估（Social Analysis）</span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="includeNews"
                  checked={form.includeNews}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                <span>包含新闻分析（News Analysis）</span>
              </label>
            </div>

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? '分析中...' : '提交分析请求'}
            </button>
          </form>

          {analysisStatus && (
            <div className="result-banner success">
              <strong>状态：{analysisStatus.status === 'queued' ? '排队中' : analysisStatus.status === 'running' ? '分析中' : analysisStatus.status}</strong>
              <br />
              股票：{analysisStatus.symbol} ({analysisStatus.market})
              {analysisStatus.started_at && (
                <>
                  <br />
                  开始时间：{new Date(analysisStatus.started_at).toLocaleString('zh-CN')}
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
