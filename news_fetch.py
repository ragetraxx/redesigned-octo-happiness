import time
import aiohttp
import asyncio
from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
from newspaper import Article
from datetime import datetime, timedelta

# Google News RSS Feed
NEWS_URL = "https://news.google.com/rss"

def fetch_rss():
    """Retrieve and parse the latest RSS news feed, filtering for today and yesterday."""
    with urlopen(NEWS_URL) as client:
        xml_page = client.read()
    
    news_items = soup(xml_page, "xml").find_all("item")
    
    # Get today's and yesterday's dates in RSS format (e.g., "Mon, 03 Mar 2025")
    today = datetime.utcnow().strftime("%a, %d %b %Y")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%a, %d %b %Y")

    # Filter news articles published today or yesterday
    return [news for news in news_items if news.pubDate.text.startswith(today) or news.pubDate.text.startswith(yesterday)]

async def fetch_article(session, link):
    """Fetch and extract content from an article asynchronously."""
    content = "Could not retrieve article content."
    try:
        article = Article(link)
        article.download()
        await asyncio.sleep(2)  # Prevent rate limiting
        if article.html:
            article.parse()
            content = article.text[:300] + "..."  # Show first 300 characters
    except Exception as e:
        content = f"Error retrieving article: {e}"
    return content

async def process_news():
    """Fetch updated news articles from today and yesterday and generate HTML output."""
    news_list = fetch_rss()

    if not news_list:
        print("No news found for today or yesterday.")
        return
    
    # Start HTML content
    html_content = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Latest News</title>
        <link rel="stylesheet" href="styles.css">
    </head>
    <body>
        <header>
            <img src="logo.png" alt="Logo" class="logo">
            <h1>Latest News</h1>
        </header>
        <div id="news-container">
    """
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_article(session, news.link.text) for news in news_list]
        contents = await asyncio.gather(*tasks)

        # Generate HTML for each news item
        for i, news in enumerate(news_list):
            title = news.title.text
            link = news.link.text
            pub_date = news.pubDate.text
            content = contents[i]  # Get the fetched content
            
            html_content += f"""
                <div class="news-item">
                    <h3>{title}</h3>
                    <p><strong>{pub_date}</strong></p>
                    <p>{content}</p>
                    <a href="{link}" target="_blank">Read more</a>
                </div>
            """
    
    # Close HTML content
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # Save to file
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    
    print("Latest news page generated: index.html")

# Run the async process
asyncio.run(process_news())