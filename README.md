# joke-api-fetcher
A lightweight Python library that provides a local joke server API. Clients can request jokes through a simple interface while the server handles fetching from JokeAPI.

Examples:
from joke_api_fetcher import client.main
mycl = JokeClient()
mycl.set_token("sometoken")
mycl.set_port(9080)
mycl.set_host("host.sld.tld")
mycl.get_joke()