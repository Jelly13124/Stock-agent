from __future__ import annotations

import os
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import analysis runner
from backend.utils.analysis_runner import run_stock_analysis, format_analysis_results


def create_app() -> Flask:
    app = Flask(__name__)
    
    # Enable CORS for frontend development (React on localhost:5173)
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # In-memory storage for analysis results (use Redis/DB in production)
    analysis_store: Dict[str, Dict[str, Any]] = {}

    @app.get("/health")
    def health() -> Any:
        """Basic healthcheck endpoint used by the React client and monitoring."""
        return jsonify({"status": "ok", "service": "manbo-investment-backend"})

    @dataclass
    class AnalysisRequest:
        symbol: str
        market: str
        research_depth: int
        llm_provider: str | None = None
        analysts: list[str] | None = None
        analysis_date: str | None = None
        include_risk_assessment: bool = True

        @classmethod
        def from_payload(cls, payload: Dict[str, Any]) -> "AnalysisRequest":
            return cls(
                symbol=payload.get("symbol", "").strip(),
                market=payload.get("market", "").strip(),
                research_depth=int(payload.get("research_depth", 1)),
                llm_provider=payload.get("llm_provider"),
                analysts=payload.get("analysts", ["market", "fundamentals", "news", "social"]),
                analysis_date=payload.get("analysis_date", datetime.now().strftime('%Y-%m-%d')),
                include_risk_assessment=payload.get("include_risk_assessment", True),
            )

    def run_analysis_async(analysis_id: str, request_data: AnalysisRequest):
        """Run analysis in background thread."""
        try:
            # Update status to running
            analysis_store[analysis_id]["status"] = "running"
            analysis_store[analysis_id]["started_at"] = datetime.now().isoformat()
            
            # Run the actual analysis
            result = run_stock_analysis(
                stock_symbol=request_data.symbol,
                analysis_date=request_data.analysis_date or datetime.now().strftime('%Y-%m-%d'),
                analysts=request_data.analysts or ["market", "fundamentals", "news", "social"],
                research_depth=request_data.research_depth,
                market_type=request_data.market,
                llm_provider=request_data.llm_provider,
                include_risk_assessment=request_data.include_risk_assessment,
                progress_callback=None  # Could implement WebSocket push here
            )
            
            # Format results
            formatted_result = format_analysis_results(result)
            
            # Extract market data for charting (if available)
            market_data = None
            try:
                # Try to extract OHLC data from the raw result
                if 'market_data' in result:
                    market_data = result.get('market_data')
                elif 'state' in result and 'market_data' in result['state']:
                    market_data = result['state'].get('market_data')
            except Exception as e:
                pass  # Market data extraction is optional
            
            # Flatten the structure for frontend
            # Frontend expects: {action, target_price, market_report, ...}
            # But format_analysis_results returns: {decision: {action, ...}, state: {market_report, ...}}
            flattened_result = {
                "success": formatted_result.get('success', False),
                **formatted_result.get('decision', {}),  # Flatten decision
                **formatted_result.get('state', {}),     # Flatten state
            }
            if 'error' in formatted_result:
                flattened_result['error'] = formatted_result['error']
            if market_data:
                flattened_result['market_data'] = market_data
            
            # Update store
            analysis_store[analysis_id].update({
                "status": "completed" if formatted_result.get('success', False) else "failed",
                "result": flattened_result,
                "completed_at": datetime.now().isoformat(),
                "error": formatted_result.get('error') if not formatted_result.get('success', False) else None
            })
            
        except Exception as e:
            analysis_store[analysis_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })

    @app.post("/analysis")
    def create_analysis() -> Any:
        """Create a new stock analysis task.
        
        This endpoint queues a real analysis job using the existing
        TradingAgents engine. The analysis runs asynchronously in a
        background thread.
        """

        payload = request.get_json(silent=True) or {}
        try:
            analysis_request = AnalysisRequest.from_payload(payload)
        except (TypeError, ValueError) as exc:  # pragma: no cover
            return jsonify({"error": f"invalid payload: {exc}"}), 400

        if not analysis_request.symbol:
            return jsonify({"error": "symbol is required"}), 400
        if not analysis_request.market:
            return jsonify({"error": "market is required"}), 400

        # Generate unique analysis ID
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize analysis record
        analysis_store[analysis_id] = {
            "id": analysis_id,
            "status": "queued",
            "symbol": analysis_request.symbol,
            "market": analysis_request.market,
            "research_depth": analysis_request.research_depth,
            "llm_provider": analysis_request.llm_provider,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=run_analysis_async,
            args=(analysis_id, analysis_request),
            daemon=True
        )
        thread.start()
        
        return (
            jsonify(
                {
                    "analysis_id": analysis_id,
                    "status": "queued",
                    "message": "分析已排队，正在处理中...",
                    "symbol": analysis_request.symbol,
                    "status_url": f"/analysis/{analysis_id}/status",
                    "result_url": f"/analysis/{analysis_id}"
                }
            ),
            202,
        )
    
    @app.get("/analysis/<analysis_id>/status")
    def get_analysis_status(analysis_id: str) -> Any:
        """Get the current status of an analysis."""
        if analysis_id not in analysis_store:
            return jsonify({"error": "Analysis not found"}), 404
        
        analysis = analysis_store[analysis_id]
        return jsonify({
            "id": analysis["id"],
            "status": analysis["status"],
            "symbol": analysis["symbol"],
            "market": analysis["market"],
            "created_at": analysis["created_at"],
            "started_at": analysis["started_at"],
            "completed_at": analysis["completed_at"],
            "has_result": analysis["result"] is not None,
            "error": analysis["error"]
        })
    
    @app.get("/analysis/<analysis_id>")
    def get_analysis_result(analysis_id: str) -> Any:
        """Get the full result of a completed analysis."""
        if analysis_id not in analysis_store:
            return jsonify({"error": "Analysis not found"}), 404
        
        analysis = analysis_store[analysis_id]
        
        if analysis["status"] == "queued" or analysis["status"] == "running":
            return jsonify({
                "id": analysis["id"],
                "status": analysis["status"],
                "message": "分析仍在进行中，请稍后查询"
            }), 202
        
        if analysis["status"] == "failed":
            return jsonify({
                "id": analysis["id"],
                "status": "failed",
                "error": analysis["error"]
            }), 500
        
        return jsonify({
            "id": analysis["id"],
            "status": analysis["status"],
            "symbol": analysis["symbol"],
            "market": analysis["market"],
            "research_depth": analysis["research_depth"],
            "llm_provider": analysis["llm_provider"],
            "created_at": analysis["created_at"],
            "completed_at": analysis["completed_at"],
            "result": analysis["result"]
        })

    return app


app = create_app()


if __name__ == "__main__":
    # Note: use_reloader=False to prevent losing in-memory analysis data on file changes
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True, use_reloader=False)
