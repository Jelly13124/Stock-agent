import os
import praw
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('dataflows')

def get_reddit_client() -> Optional[praw.Reddit]:
    """Initialize and return a Reddit API client."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "TradingAgents/1.0")
    
    if not client_id or not client_secret:
        # Only log warning once or if explicitly debugging to avoid log spam
        # logger.warning("Reddit API credentials not found.") 
        return None
        
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        return reddit
    except Exception as e:
        logger.error(f"Failed to initialize Reddit client: {e}")
        return None

def fetch_top_from_category(category: str = 'investing', limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch top posts from a specific subreddit category."""
    reddit = get_reddit_client()
    if not reddit:
        return []
        
    try:
        subreddit = reddit.subreddit(category)
        posts = []
        for post in subreddit.top(time_filter='week', limit=limit):
            posts.append({
                'title': post.title,
                'score': post.score,
                'url': post.url,
                'created_utc': post.created_utc,
                'num_comments': post.num_comments,
                'selftext': post.selftext[:500] + "..." if len(post.selftext) > 500 else post.selftext
            })
        return posts
    except Exception as e:
        logger.error(f"Error fetching top posts from {category}: {e}")
        return []

def get_reddit_global_news(curr_date: str, look_back_days: int = 7) -> str:
    """Get global financial news/discussions from Reddit.
    
    Args:
        curr_date: Current date in YYYY-MM-DD format
        look_back_days: Number of days to look back
    """
    reddit = get_reddit_client()
    if not reddit:
        return "Reddit API not configured. Unable to fetch Reddit news."

    # Logic to fetch from r/investing, r/stocks, r/finance, r/economics
    subreddits = ['economics', 'finance', 'investing', 'stocks', 'wallstreetbets']
    results = []
    
    try:
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            posts_found = 0
            # Fetch hot/top posts
            for post in subreddit.hot(limit=5):
                results.append(f"### r/{sub}: {post.title} (Score: {post.score})\n{post.selftext[:800]}\n")
                posts_found += 1
            
            if posts_found == 0:
                 pass
                 
        if not results:
            return "No relevant global Reddit news found."
            
        return "## Global Market Discussions from Reddit:\n\n" + "\n\n".join(results)
        
    except Exception as e:
        logger.error(f"Error fetching global Reddit news: {e}")
        return f"Error fetching Reddit news: {str(e)}"

def get_reddit_company_news(ticker: str, curr_date: str, look_back_days: int = 7) -> str:
    """Get company specific discussions from Reddit.
    
    Args:
        ticker: Stock ticker symbol
        curr_date: Current date in YYYY-MM-DD format
        look_back_days: Number of days to look back
    """
    reddit = get_reddit_client()
    if not reddit:
        return f"Reddit API not configured. Unable to fetch discussions for {ticker}."
        
    try:
        # Search for ticker in relevant subreddits
        query = f"{ticker}"
        results = []
        
        # Search broadly
        search_results = reddit.subreddit("all").search(query, sort='relevance', time_filter='week', limit=15)
        
        for submission in search_results:
             # Filter out posts with very low scores to reduce noise
             if submission.score < 5:
                 continue
                 
             content = submission.selftext[:800] + ("..." if len(submission.selftext) > 800 else "")
             # If no selftext, use title (often link posts)
             if not content:
                 content = "(Link Post)"
                 
             results.append(f"### {submission.title} (Score: {submission.score}, Sub: r/{submission.subreddit})\n{content}\n")
             
        if not results:
             return f"No significant Reddit discussions found for {ticker} in the past week."
             
        return f"## Reddit Discussions for {ticker}:\n\n" + "\n\n".join(results)
    except Exception as e:
        logger.error(f"Error searching Reddit for {ticker}: {e}")
        return f"Error fetching Reddit data for {ticker}: {e}"

def get_reddit_stock_info(ticker: str) -> str:
    """Alias for get_reddit_company_news used in some configs"""
    # Use today's date as default
    return get_reddit_company_news(ticker, datetime.now().strftime('%Y-%m-%d'))
    
def get_reddit_sentiment(ticker: str) -> str:
     """Get sentiment for a ticker (alias for company news for now)"""
     return get_reddit_company_news(ticker, datetime.now().strftime('%Y-%m-%d'))

