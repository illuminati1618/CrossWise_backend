from __init__ import db

class BorderTweet(db.Model):
    __tablename__ = "border_tweets"

    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.String, unique=True)
    author_id = db.Column(db.String)
    created_at = db.Column(db.String)
    query = db.Column(db.String)
    text = db.Column(db.Text)
    score = db.Column(db.Float)  # Placeholder for Gemini AI score

    def __init__(self, tweet_id, author_id, created_at, query, text, score=None):
        self.tweet_id = tweet_id
        self.author_id = author_id
        self.created_at = created_at
        self.query = query
        self.text = text
        self.score = score

    def __repr__(self):
        return f"<BorderTweet {self.tweet_id}>"

    def save(self):
        if not BorderTweet.query.filter_by(tweet_id=self.tweet_id).first():
            db.session.add(self)
            db.session.commit()
