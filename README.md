# redis-cache-extraction
This repo contains script `makecache.py` that generate predefined cache for
Orange-imageanalytics embedders.

How to build a predefined cache?

1. Place the images to get cached into images directory

2. Run embedders to fill the cache

       ORANGE_EMBEDDING_API_URL=<dev url> python run_embedders.py

3. Retrieve redis database dump:

       ssh <dev server>
       POD=$(kubectl get pod | grep redis-redis | awk '{print $1;}')
       kubectl cp default/$POD:/bitnami/redis/data/dump.rdb dump.rdb

4. Move dump.rdb to `tmp` directory in this project

5. Run script to generate redis cache

       python makecache.py



