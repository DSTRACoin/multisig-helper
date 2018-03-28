"""
  Copyright (C) 2017 Oleksii Ivanchuk

  This file is part of slick-bitcoinrpc.
  It is subject to the license terms in the LICENSE file found in the
  top-level
  directory of this distribution.

  No part of slick-bitcoinrpc, including this file, may be copied, modified,
  propagated, or distributed except according to the terms contained in the
  LICENSE file

  Copyright (C) 2018 Masao Hidemitsu
"""

from itertools import count
from json.decoder import JSONDecodeError
from urllib.parse import urlparse

import requests
from configobj import ConfigObj
from requests.auth import HTTPBasicAuth

from .exceptions import RpcException

DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_RPC_PORT = 8332


class Proxy:
    _ids = count(0)

    def __init__(self,
                 service_url=None,
                 service_port=None,
                 conf_file=None,
                 timeout=DEFAULT_HTTP_TIMEOUT):
        config = {}
        if conf_file:
            config = ConfigObj(conf_file)
        if service_url:
            config.update(self.url_to_conf(service_url))
        if service_port:
            config.update(rpcport=service_port)
        elif not config.get('rpcport'):
            config['rpcport'] = DEFAULT_RPC_PORT

        self.auth = HTTPBasicAuth(config['rpcuser'], config['rpcpassword'])
        self.base_url = f'http://{config["rpchost"]}:{config["rpcport"]}'
        self.timeout = timeout

    def __getattr__(self, method):
        id = next(self._ids)
        base_url = self.base_url
        auth = self.auth
        timeout = self.timeout

        def call(*params):
            resp = requests.post(
                base_url,
                json={"jsonrpc": "2.0",
                      "method": method,
                      "params": params,
                      "id": id},
                auth=auth,
                timeout=timeout
            )

            try:
                r = resp.json()
            except JSONDecodeError:
                print(resp.content)
                raise RuntimeError(f'something went wrong: {resp.content}')

            if r.get('error') is not None:
                raise RpcException(r['error'], method, params)
            return r['result']

        return call

    @staticmethod
    def url_to_conf(service_url):
        url = urlparse(service_url)
        return dict(rpchost=url.hostname, rpcport=url.port,
                    rpcuser=url.username, rpcpassword=url.password)
