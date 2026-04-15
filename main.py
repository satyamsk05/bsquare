from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

from app.fetchers.news_fetcher import get_latest_news
from app.fetchers.gainers_fetcher import get_top_gainers
from app.core.content_writer import write_gainers_post, write_news_post
from app.core.square_poster import post_to_square
from app.utils.telegram_notify import notify
from app.utils.telegram_approval import request_news_approval
from app.config import NEWS_POST_HOUR, GAINERS_INTERVAL_HOURS
from app.database import db_init, log_post


# ── GAINERS — Direct post, no approval needed ──────────────────
def run_gainers_post():
    print(f"\n[{datetime.now()}] Running gainers post...")

    gainers = get_top_gainers()
    if not gainers:
        print("No gainers data, skipping.")
        notify("Gainers bot: Could not fetch data, skipping post.")
        return

    content = write_gainers_post(gainers)
    print(f"\nGenerated Gainers Post:\n{content}\n")

    url = post_to_square(content)
    if url:
        # Gainers source_id is timestamp because it changes every time
        source_id = f"gainers_{datetime.now().strftime('%Y-%m-%d_%H')}"
        log_post(source_id, content, url)
        notify(f"✅ Gainers post published\n{url}")
    else:
        notify("❌ Gainers post FAILED. Check logs.")


# ── NEWS — Telegram approval required ─────────────────────────
def run_news_post():
    print(f"\n[{datetime.now()}] Running news post...")

    news = get_latest_news()
    if not news:
        print("No new news found, skipping.")
        return

    # Generator function — Refresh button ke liye naya post banana
    def generate_fresh(sentiment: str = None):
        fresh_news = get_latest_news()
        if not fresh_news:
            raise Exception("No more fresh news available")
        return write_news_post(fresh_news, forced_sentiment=sentiment)

    # Post mapping with logging
    def post_and_log(text):
        url = post_to_square(text)
        if url:
            log_post(news["url"], text, url)
        return url

    # Pehla post generate karo
    content = write_news_post(news)
    print(f"\nGenerated News Post (pending approval):\n{content}\n")

    # Telegram pe approval maango
    request_news_approval(
        post_content=content,
        generate_fn=generate_fresh,
        post_fn=post_and_log,
    )


if __name__ == "__main__":
    print("Bot starting...")
    
    # Database initialize karo
    db_init()
    
    notify("🤖 Binance Square Bot started!")

    # Pehli baar turant chalao
    run_gainers_post()
    run_news_post()

    # Schedule karo
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # News — roz subah 9 baje
    scheduler.add_job(run_news_post, "cron", hour=NEWS_POST_HOUR, minute=0)

    # Gainers — har 12 ghante
    scheduler.add_job(run_gainers_post, "interval", hours=GAINERS_INTERVAL_HOURS)

    print(f"Scheduler running — News at {NEWS_POST_HOUR}:00 IST, Gainers every {GAINERS_INTERVAL_HOURS}hrs")
    scheduler.start()
