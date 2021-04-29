# Core App

## Have GOT to get a handle on "database is locked" errors

## Dark Mode

See https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme for details

## Handle custom error pages

## More tests for normalize

## Uniformly localized dates/times on the frontend

## Normalize and store enclosures on entries

## Crawling support for feed-level crawling hints (TTL, etc)

## Fetching favicons for sites that don't include them in the feeds

## Fetching full articles?

# Deployment

## SQLite3 on NFS is a bad plan

Currently pinned to a specific cluster node because otherwise, no amount of
concurrency will work.  Still need to work on the "database is locked" problem.

Could possibly bring back iSCSI volumes to see if it corrects the locking issue,
but iSCSI can't be mounted in multiple pods at a time.  If I do try iSCSI, I'll
need to make crawling something that happens _within_ the same process as the
web server.  They should be able to share the same event loop, but contention
may be a bit of an issue.
