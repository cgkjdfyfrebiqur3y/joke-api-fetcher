# joke-api-fetcher

![PyPI](https://img.shields.io/pypi/v/joke-api-fetcher)
![Python](https://img.shields.io/pypi/pyversions/joke-api-fetcher)

A lightweight Python library that provides a local joke server API. Clients can request jokes through a simple interface while the server handles fetching from JokeAPI.



# This project is new. If you use it, please try to break it and report anything strange.

Examples:
from joke_api_fetcher.client.main import JokeClient
mycl = JokeClient()
mycl.set_token("sometoken")
mycl.set_port(9080)
mycl.set_host("host.sld.tld")
mycl.getjoke()
