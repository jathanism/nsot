###################
React Web UI Readme
###################

Caveats
=======

- The NSoT server has ``APPEND_SLASH = False`` set for now to simplify URL routing on the front-end
- There's a bunch of CORS stuff hard-coded in the NSoT settings, too
- You must be running the localhost proxy server (user_proxy on port 8991)

Running the React app
=====================

NSoT
----

(From project root so local code changes can be picked up)

Server::

    ./nsot-server runserver 0.0.0.0:8990 --insecure

Proxy::

    ./nsot-server user_proxy -P 8990 -p 8991 -a 0.0.0.0

App
---

(From project root, first ``cd react`` so you're in the react dir)

The app server is running on a different port and talking to NSoT using CORS *for now*

React app server::

    python manage.py 0.0.0.0:8124 --insecure

Webpack::

    ./node_modules/.bin/webpack --config webpack.config.js --watch --watch-poll --display-error-details
