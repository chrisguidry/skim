skim, a self-hosted news reader
===============================

Directory structure
-------------------

    .skim
    |- subscriptions.opml                   # subscriptions and categories
    |- feed-slug-a                          # a single feed
    |  |- conditional-get                   # conditional GET state
    |  |- feed.json                         # feed metadata
    |  |- entries.db                        # entry slugs by URL, for deduplication
    |  |- YYYY-MM-DDTHH:MM:SS-entry-slug-a  # a single entry
    |  |  |- entry.json                     # entry metadata
    |  |  |- body.md                        # markdown version
    |  |  |- body.html                      # (cached) HTML version
    |  |  |- image-a.png                    # locally cached image
    |  |  |- ...
    |  |- YYYY-MM-DDTHH:MM:SS-entry-slug-b
    |  |- ...
    |- feed-slug-b
    |- ...
    |- index
       |- timeseries.sqlite3                # the master timeseries of entries
       |- search index files                # Whoosh search index files
