CREATE INDEX crawl_log_crawled ON crawl_log (crawled DESC);
CREATE INDEX crawl_log_feed_crawled ON crawl_log (feed, crawled DESC);
