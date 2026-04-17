import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# --- Database Setup ---
# Note: We will replace 'YOUR_NEW_ENDPOINT' in a few minutes
DB_URL = "postgresql://postgres:BoozAllen2026!@YOUR_NEW_ENDPOINT:5432/postgres"
engine = create_engine(DB_URL)
Base = declarative_base()

# Define the table structure for your SQL DB
class SentimentResult(Base):
    __tablename__ = 'sentiment_results'
    id = Column(Integer, primary_key=True)
    company = Column(String)
    headline = Column(String)
    sentiment_score = Column(Float)

# Create the table if it doesn't exist
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_sentiment(text):
    # Simple logic for the lab
    pos = ["surge", "profit", "gain", "growth", "success"]
    neg = ["scandal", "loss", "lawsuit", "drop", "failure"]
    score = 0
    for word in pos:
        if word in text.lower(): score += 1
    for word in neg:
        if word in text.lower(): score -= 1
    return score

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    company = data.get('company', 'Amazon')
    
    # Configure Selenium for the Docker environment
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    
    # Scrape Google News
    driver.get(f"https://www.google.com/search?q={company}+news&tbm=nws")
    headlines = driver.find_elements("css selector", "div.BNeawe.vvv7qc.u30dYd.xtS6pe")
    
    session = Session()
    results = []
    for h in headlines[:3]:
        text = h.text
        score = get_sentiment(text)
        # Save to RDS Table
        res = SentimentResult(company=company, headline=text, sentiment_score=score)
        session.add(res)
        results.append({"headline": text, "score": score})
    
    session.commit()
    session.close()
    driver.quit()
    return jsonify({"status": "Success", "company": company, "results": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
