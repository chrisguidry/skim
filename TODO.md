# Core App

## Have GOT to get a handle on "database is locked" errors

## Handle custom error pages

## Uniformly localized dates/times on the frontend

## Normalize and store enclosures on entries

## Crawling support for feed-level crawling hints (TTL, etc)

## Fetching favicons for sites that don't include them in the feeds

## Wrap plain text articles in markup

Plain text articles don't pick up the `<p>` top and bottom margins, so they
appears to be sitting too high in the feed.

## Fetching full articles?

## Caching images?

## A quick way to jump to the next article?

First, does this violate the spirit of skim?  If not, then it would be nice
to pop ahead to the next article instead of scrolling a potentially long one.

# Deployment

## SQLite3 on NFS is a bad plan

Currently pinned to a specific cluster node because otherwise, no amount of
concurrency will work.  Still need to work on the "database is locked" problem.

Could possibly bring back iSCSI volumes to see if it corrects the locking issue,
but iSCSI can't be mounted in multiple pods at a time.  If I do try iSCSI, I'll
need to make crawling something that happens _within_ the same process as the
web server.  They should be able to share the same event loop, but contention
may be a bit of an issue.

## Automated backups
