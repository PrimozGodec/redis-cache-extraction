# redis-cache-extraction
This repo contains script `makecache.py` that generate predefined cache for
Orange-imageanalytics embedders.

How to build a predefined cache?

Run embedders to fill the cache

    ORANGE_EMBEDDING_API_URL=<dev url> python run_embedders.py

Retrieve redis database dump:

    ssh <dev server>
    POD=$(kubectl get pod | grep redis-redis | awk '{print $1;}')
    kubectl cp default/$POD:/bitnami/redis/data/dump.rdb dump.rdb

Move dump.rdb to `tmp` directory in this project and run script to generate
redis predefined cache.



