import os
import time
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = Flask(__name__)

# --- Database Setup ---
DB_URL = "postgresql://postgres:BoozAllen2026!@sentiment-db-v2.ch4ecygo0rze.us-east-1.rds.amazonaws.com:5432/postgres"
engine = create_engine(DB_URL)
Base = declarative_base()

class SentimentResult(Base):
    __tablename__ = 'sentiment_results'
    id = Column(Integer, primary_key=True)
    company = Column(String)
    headline = Column(String)
    sentiment_score = Column(Float)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_sentiment(text):
    pos = ["surge", "profit", "gain", "growth", "success", "ai", "new"]
    neg = ["scandal", "loss", "lawsuit", "drop", "failure", "layoff"]
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
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Use a real User-Agent to avoid the "empty" response
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    # Scrape Google News
    driver.get(f"https://www.google.com/search?q={company}+news&tbm=nws")
    time.sleep(2) # Give it a second to render
    
    # Try the most common 2026 selectors
    # h3 is standard for headlines; MBeuO is the current desktop class
    headlines = driver.find_elements(By.CSS_SELECTOR, "div.MBeuO, h3, div.BNeawe")
    
    session = Session()
    results = []
    
    # Only process if we actually found something
    for h in headlines[:5]:
        text = h.text
        if len(text) > 10: # Filter out noise
            score = get_sentiment(text)
            res = SentimentResult(company=company, headline=text, sentiment_score=score)
            session.add(res)
            results.append({"headline": text, "score": score})
    
    session.commit()
    session.close()
    driver.quit()
    
    return jsonify({
        "status": "Success", 
        "count": len(results),
        "company": company, 
        "results": results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)   
