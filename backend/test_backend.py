"""Quick test script for the Flask backend endpoints."""
from app import app


def test_endpoints():
    """Test health and analysis endpoints."""
    with app.test_client() as client:
        # Test health endpoint
        health = client.get('/health')
        print(f'✅ GET /health -> {health.status_code}')
        print(f'   Response: {health.json}')
        print()

        # Test analysis endpoint with valid payload
        ok_response = client.post('/analysis', json={
            'symbol': 'AAPL',
            'market': '美股',
            'research_depth': 2,
            'llm_provider': 'google'
        })
        print(f'✅ POST /analysis (valid) -> {ok_response.status_code}')
        print(f'   Response: {ok_response.json}')
        print()

        # Test analysis endpoint with missing symbol
        bad_response = client.post('/analysis', json={'market': '美股'})
        print(f'❌ POST /analysis (missing symbol) -> {bad_response.status_code}')
        print(f'   Response: {bad_response.json}')
        print()

        # Test analysis endpoint with missing market
        bad2_response = client.post('/analysis', json={'symbol': 'TSLA'})
        print(f'❌ POST /analysis (missing market) -> {bad2_response.status_code}')
        print(f'   Response: {bad2_response.json}')


if __name__ == '__main__':
    test_endpoints()

