if __name__ == '__main__':  # pragma: no cover
    from skim import configure_metrics, server

    configure_metrics()

    server.run()
