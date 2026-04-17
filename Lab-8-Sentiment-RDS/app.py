# ... (Keep the imports and Database Setup exactly as they are)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    company = data.get('company', 'Amazon')
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # NEW: Stealth flags to bypass bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    # NEW: Use the official Google News search endpoint (cleaner for scrapers)
    news_url = f"https://news.google.com/search?q={company}&hl=en-US&gl=US&ceid=US:en"
    driver.get(news_url)
    time.sleep(3) # Wait slightly longer for JS to render
    
    # NEW: Better 2026 Desktop Selectors (targeting the article tags)
    # On Google News, headlines are almost always in <h3> or <a> within an <article>
    headlines = driver.find_elements(By.CSS_SELECTOR, "article h3, article a, h3")
    
    session = Session()
    results = []
    
    for h in headlines:
        text = h.text.strip()
        # Filter: Only take long strings and avoid duplicates
        if len(text) > 20 and text not in [r["headline"] for r in results]:
            score = get_sentiment(text)
            res = SentimentResult(company=company, headline=text, sentiment_score=score)
            session.add(res)
            results.append({"headline": text, "score": score})
        
        if len(results) >= 5: break # Cap at 5 results
    
    session.commit()
    session.close()
    driver.quit()
    
    return jsonify({
        "status": "Success", 
        "count": len(results),
        "company": company, 
        "results": results
    })

# ... (Keep the rest of the file)
