CREATE TABLE crawl_log (
    feed TEXT NOT NULL,
    crawled TEXT NOT NULL,
    status INT NULL,
    content_type TEXT NULL,
    new_entries INT NULL
);
