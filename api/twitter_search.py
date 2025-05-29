import os
import requests
from dotenv import load_dotenv
from model.twitter import BorderTweet
from flask import current_app

# Load environment variables
load_dotenv(dotenv_path='instance/.env')

# Twitter API setup
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

def search_tweets(query="Otay Mesa border wait", max_results=10):
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "created_at,author_id,text"
    }
    response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise Exception(f"Twitter API error {response.status_code}: {response.text}")
    return response.json().get("data", [])

def run_border_queries():
    print("🔍 Scraping Twitter for border-related keywords...\n")
    keywords = [
        "Otay Mesa border wait", 
        "San Ysidro crossing delay", 
        "Tijuana border crossing", 
        "Otay line long", 
        "crossed San Ysidro today"
    ]

    with current_app.app_context():
        for query in keywords:
            print(f"\n🔎 Query: {query}")
            try:
                tweets = search_tweets(query=query, max_results=10)
                for tweet in tweets:
                    print(f"@{tweet['author_id']} [{tweet['created_at']}]: {tweet['text'][:120]}...")
                    tweet_obj = BorderTweet(
                        tweet_id=tweet['id'],
                        author_id=tweet['author_id'],
                        created_at=tweet['created_at'],
                        query=query,
                        text=tweet['text'],
                        score=None  # Placeholder for Gemini score later
                    )
                    tweet_obj.save()
            except Exception as e:
                print(f"❌ Failed on query '{query}': {e}")
