export interface HealthResponse {
  status: string
  service: string
}

export interface CreateAnalysisPayload {
  symbol: string
  market: string
  research_depth: number
  llm_provider?: string
  analysts?: string[]
  analysis_date?: string
  include_risk_assessment?: boolean
}

export interface CreateAnalysisResponse {
  analysis_id: string
  status: string
  message: string
  symbol: string
  status_url: string
  result_url: string
}

export interface AnalysisStatus {
  id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  symbol: string
  market: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  has_result: boolean
  error: string | null
}

export interface AnalysisResult {
  id: string
  status: string
  symbol: string
  market: string
  research_depth: number
  llm_provider: string | null
  created_at: string
  completed_at: string | null
  result: {
    success: boolean
    action?: string
    target_price?: number | null
    confidence?: number
    risk_score?: number
    reasoning?: string
    market_report?: string
    fundamentals_report?: string
    news_report?: string
    risk_assessment?: string
    investment_debate_state?: string
    trader_investment_plan?: string
    risk_debate_state?: string
    final_trade_decision?: string
    market_data?: Array<{
      date: string
      open?: number
      high?: number
      low?: number
      close: number
      volume?: number
    }>
    error?: string
  } | null
}

const DEFAULT_API_BASE = 'http://localhost:8000'

const resolveBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${resolveBaseUrl()}/health`)
  if (!response.ok) {
    throw new Error(`Failed to fetch health: ${response.status}`)
  }
  return (await response.json()) as HealthResponse
}

export async function createAnalysis(
  payload: CreateAnalysisPayload
): Promise<CreateAnalysisResponse> {
  const response = await fetch(`${resolveBaseUrl()}/analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}))
    const message = typeof errorPayload.error === 'string' ? errorPayload.error : 'unknown error'
    throw new Error(`Analysis request failed: ${message}`)
  }

  return (await response.json()) as CreateAnalysisResponse
}

export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
  const response = await fetch(`${resolveBaseUrl()}/analysis/${analysisId}/status`)
  if (!response.ok) {
    throw new Error(`Failed to fetch status: ${response.status}`)
  }
  return (await response.json()) as AnalysisStatus
}

export async function getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
  const response = await fetch(`${resolveBaseUrl()}/analysis/${analysisId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch result: ${response.status}`)
  }
  return (await response.json()) as AnalysisResult
}
