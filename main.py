import logging
import time
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from app.fetchers.news_fetcher import get_latest_news
from app.fetchers.gainers_fetcher import get_top_gainers
from app.core.content_writer import write_gainers_post, write_news_post
from app.core.square_poster import post_to_square
from app.utils.telegram_notify import notify
from app.utils.telegram_approval import request_news_approval
from app.config import NEWS_POST_HOUR, GAINERS_INTERVAL_HOURS, validate_config
from app.database import db_init, log_post

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger("main")

# ── GAINERS — Direct post, no approval needed ──────────────────
def run_gainers_post():
    logger.info("Running gainers post job...")
    try:
        gainers = get_top_gainers()
        if not gainers:
            logger.warning("No gainers data found, skipping.")
            notify("Gainers bot: Could not fetch data, skipping post.")
            return

        content = write_gainers_post(gainers)
        logger.info(f"Generated Gainers Post:\n{content}")

        url = post_to_square(content)
        if url:
            # Gainers source_id is timestamp because it changes every time
            source_id = f"gainers_{datetime.now().strftime('%Y-%m-%d_%H')}"
            log_post(source_id, content, url)
            notify(f"✅ Gainers post published\n{url}")
            logger.info(f"Gainers post published: {url}")
        else:
            notify("❌ Gainers post FAILED. Check logs.")
            logger.error("Gainers post failed at the posting stage.")
    except Exception as e:
        logger.error(f"Error in run_gainers_post: {e}", exc_info=True)

# ── NEWS — Telegram approval required ─────────────────────────
def run_news_post():
    logger.info("Running news post job...")
    try:
        news = get_latest_news()
        if not news:
            logger.info("No new news found, skipping.")
            return

        # Keep track of which news item is currently being approved.
        current_news = news
        current_source_id = news.get("url")
        exclude_ids = {current_source_id} if current_source_id else set()

        # Generator function:
        # - Refresh button: fetch next unseen article in this session
        # - Tone selection: regenerate for the same article with forced sentiment
        def generate_fresh(sentiment: str = None):
            nonlocal current_news, current_source_id
            if sentiment:
                return write_news_post(current_news, forced_sentiment=sentiment)

            fresh_news = get_latest_news(exclude_ids=exclude_ids)
            if not fresh_news:
                raise Exception("No more fresh news available")

            fresh_id = fresh_news.get("url")
            if fresh_id:
                exclude_ids.add(fresh_id)
                current_source_id = fresh_id
            current_news = fresh_news
            return write_news_post(current_news)

        # Post mapping with correct source_id logging (even after Refresh/Tone).
        def post_and_log(text):
            url = post_to_square(text)
            if url and current_source_id:
                log_post(current_source_id, text, url)
            return url

        # Pehla post generate karo
        content = write_news_post(current_news)
        logger.info("Generated initial news post, waiting for approval...")

        # Telegram pe approval maango (This is a blocking call)
        request_news_approval(
            post_content=content,
            generate_fn=generate_fresh,
            post_fn=post_and_log,
        )
    except Exception as e:
        logger.error(f"Error in run_news_post: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("=== Binance Square Bot Starting ===")

    # Validate runtime requirements for running the bot end-to-end.
    validate_config(require_square=True, require_ai=True, require_telegram=True)
    
    # Database initialize karo
    db_init()
    
    notify("🤖 Binance Square Bot started!")

    # Initial run (Optional, can be commented out if not needed on every restart)
    logger.info("Performing initial run...")
    run_gainers_post()
    run_news_post()

    # Scheduler setup
    # We use a ThreadPoolExecutor to ensure blocking jobs don't stop the scheduler
    executors = {
        'default': ThreadPoolExecutor(20)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3,
        'misfire_grace_time': 3600
    }
    
    scheduler = BlockingScheduler(
        timezone="Asia/Kolkata", 
        executors=executors, 
        job_defaults=job_defaults
    )

    # News — roz subah 9 baje
    scheduler.add_job(
        run_news_post, 
        "cron", 
        hour=NEWS_POST_HOUR, 
        minute=0, 
        id="news_job"
    )

    # Gainers — har 12 ghante
    scheduler.add_job(
        run_gainers_post, 
        "interval", 
        hours=GAINERS_INTERVAL_HOURS, 
        id="gainers_job"
    )

    logger.info(f"Scheduler started: News at {NEWS_POST_HOUR}:00 IST, Gainers every {GAINERS_INTERVAL_HOURS}hrs")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutting down...")
