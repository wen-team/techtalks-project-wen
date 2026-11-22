# wen
Lebanese address resolution: free-text directions to map locations

# Project Setup

In order to run the dev docker image, please create a ```.env.dev``` file according to the ```.env.example``` file and populate it.

After that is done, run:

``` docker-compose --env-file techtalks_project_wen/.env.dev -f techtalks_project_wen/docker-compose.yml up -d ```

After pulling all the images, the server should be running at localhost port 8000.

Notes:
- 0.0.0.0 is not in the allowed hosts list, you may need to add it to the .env.dev if you want but localhost:8000 should suffice.
- If your django secret has a '$' character **MAKE SURE TO SUPPLY THE KEY IN THE ENV FILE LIKE THIS** : SECRET_KEY='django-insecure-<part with $>'.
- You will get a 404 when opening it in a browser because no routes have been configured yet.
- If you get no errors but the docker container just doesn't start, remove the -d argument to debug and troubleshoot.

## First run: create the database tables

Once the containers are up, run the migrations once (and again after pulling new migrations):

``` docker-compose --env-file techtalks_project_wen/.env.dev -f techtalks_project_wen/docker-compose.yml exec web python manage.py migrate ```

The frontend lives in `techtalks_project_wen/wen_web/`. See its [README](techtalks_project_wen/wen_web/README.md).
