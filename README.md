skim, a self-hosted news reader
===============================

Note that skim includes `pygments-css` (styles for code syntax highlighting) as
a git submodule.  Don't forget to run `git submodule init` after cloning for
the first time.

Running with Docker
-------------------

skim can be run as two Docker containers: one for crawling feeds and one for
serving the web reader.

Building skim
-------------

```
$ cp skim.ini.example skim.ini  # and then customize it
$ docker build -t skim:latest .
$ docker build -t skim-crawl:latest -f Dockerfile.crawl .
$ docker build -t skim-web:latest -f Dockerfile.web .
```

The containers have the following interface:

* The web container exposes HTTP over port 3333
* Both containers share feed entries and data from a volume at `/storage/`
* Both containers read and write your subscriptions to an OPML file mounted at
  `/storage/subscriptions.opml`.  If you already have an OPML file of feeds,
  you can simply place it there before starting skim.  You can also use the
  included `example.opml` to get started.


Running skim with a Docker data container
-----------------------------------------

To get a functional skim setup, with shared storage in a Docker data container:

```
$ docker create --name skim-storage -v /storage skim:latest /bin/true
```

Adding your `subscriptions.opml` file is a little awkward with a Docker data
container.  To copy it into the storage area:

```
$ docker run --rm -v ~/your.subscriptions.opml:/tmp/subscriptions.opml --volumes-from skim-storage skim:latest cp /tmp/subscriptions.opml /storage/subscriptions.opml
```

$ docker create --name skim-crawl --restart no --volumes-from skim-storage skim-crawl:latest
$ docker run -d --name skim-web --volumes-from skim-storage -p 3333:3333 skim-web:latest
$ docker start -a skim-crawl  # schedule this command via cron every 15 minutes or so
```

Running skim with external storage
----------------------------------

To store your feeds elsewhere, like a NAS volume over NFS
(`/your/storage/location/`, in this example):

```
$ cp ~/your.subscriptions.opml /your/storage/location/
$ docker create --name skim-crawl --restart no -v /your/storage/location/:/storage skim-crawl:latest
$ docker run -d --name skim-web -v /your/storage/location/:/storage -p 3333:3333 skim-web:latest
$ docker start -a skim-crawl  # schedule this command via cron every 15 minutes or so
```


Using skim
----------

You can add and remove subscriptions from ~/subscriptions.  You can export your
subscriptions as an OPML file from ~/subscriptions.opml.

Feeds retain 250 entries to keep storage from growing forever.


`/storage/` Directory structure
-------------------------------

    /storage
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
