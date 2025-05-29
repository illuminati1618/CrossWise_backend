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
    print("\n📡 [TwitterScraper] Starting scrape of border-related tweets...\n")

    keywords = [
    "Otay Mesa border wait"  # Limit to 1 query to stay within quota
]


    with current_app.app_context():
        for query in keywords:
            print(f"🔎 [QUERY] {query}")
            try:
                tweets = search_tweets(query=query, max_results=1)

                if not tweets:
                    print("   ⚠️  No tweets found.")

                for tweet in tweets:
                    tweet_id = tweet['id']
                    existing = BorderTweet.query.filter_by(tweet_id=tweet_id).first()
                    if existing:
                        print(f"   🔁 Already exists: {tweet_id}")
                        continue

                    print(f"   🐦 @{tweet['author_id']} | {tweet['created_at']} → {tweet['text'][:100]}...")
                    
                    tweet_obj = BorderTweet(
                        tweet_id=tweet['id'],
                        author_id=tweet['author_id'],
                        created_at=tweet['created_at'],
                        query=query,
                        text=tweet['text'],
                        score=None
                    )
                    tweet_obj.save()
                    print(f"   ✅ Saved to DB: {tweet_id}")

            except Exception as e:
                print(f"   ❌ Error fetching tweets for '{query}': {e}")
    
    print("\n✅ [TwitterScraper] Scrape complete.\n")
