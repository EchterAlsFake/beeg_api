"""
Copyright (C) 2025 Johannes Habel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import math
import html
import httpx
import logging
import argparse

from functools import cached_property
from typing import Union, Generator, Optional
from base_api.modules.config import RuntimeConfig
from base_api.base import BaseCore, setup_logger, Helper
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

try:
    from modules.consts import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *


class Video:
    def __init__(self, url: str, core: BaseCore):
        self.url = url
        self.core = core
        self.core.enable_logging(level=logging.DEBUG)
        self.html_content = self.core.fetch(self.url)
        self.json_data = self.core.fetch(f"https://store.externulls.com/facts/file/{self.video_id}", get_response=True).json() # This is the holy grail

    @cached_property
    def video_id(self) -> str:
        return self.url.split("/")[-1].strip("-0")




class Client:
    def __init__(self, core: BaseCore = None):
        self.core = core or BaseCore()
        self.core.initialize_session()

    def get_video(self, url: str) -> Video:
        return Video(url, core=self.core)


if __name__ == "__main__":
    client = Client()
    video = client.get_video("https://beeg.com/-0830673897358738")
