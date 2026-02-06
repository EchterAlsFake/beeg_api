"""
Copyright (C) 2025-2026 Johannes Habel

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
import logging
import threading

from typing import Optional
from functools import cached_property
from base_api.base import BaseCore, setup_logger

try:
    from modules.consts import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *


class Video:
    def __init__(self, url: str, core: BaseCore):
        self.url = url
        self.core = core
        self.json_data: dict = self.core.fetch(f"https://store.externulls.com/facts/file/{self.key}", get_response=True).json() # This is the holy grail
        self.logger = setup_logger(name="BEEG API - [Video]", log_file=None, level=logging.ERROR)

    def enable_logging(self, log_file: str = None, level=None, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="BEEG API - [Video]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    @cached_property
    def key(self) -> str:
        return self.url.split("/")[-1].strip("-0") # The video key used across the page for all APIs

    @cached_property
    def title(self) -> str:
        return self.json_data.get("file").get("data")[0].get("cd_value")

    @cached_property
    def video_id(self) -> str:
        return self.json_data.get("file").get("data")[0].get("id")

    @cached_property
    def duration(self) -> int:
        return self.json_data.get("file").get("fl_duration")

    @cached_property
    def m3u8_base_url(self) -> str:
        url = self.json_data.get("file").get("hls_resources").get("fl_cdn_multi")
        return f"https://video.externulls.com/{url}"

    def get_segments(self, quality) -> list:
        """
        :param quality: (str, Quality) The video quality
        :return: (list) A list of segments (the .ts files)
        """
        segments = self.core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)
        return segments

    def download(self, quality, path="./", callback=None, no_title=False, remux: bool = False,
                 callback_remux=None, start_segment: int = 0, stop_event: Optional[threading.Event] = None,
                 segment_state_path: Optional[str] = None, segment_dir: Optional[str] = None,
                 return_report: bool = False, cleanup_on_stop: bool = True, keep_segment_dir: bool = False
                 ) -> bool:
        """
        :param callback:
        :param quality:
        :param path:
        :param no_title:
        :param remux:
        :param callback_remux:
        :param start_segment:
        :param stop_event:
        :param segment_state_path:
        :param segment_dir:
        :param return_report:
        :param cleanup_on_stop:
        :param keep_segment_dir:
        :return:
        """
        if not no_title:
            path = os.path.join(path, f"{self.title}.mp4")

        return self.core.download(video=self, quality=quality, path=path, callback=callback, remux=remux,
                                  callback_remux=callback_remux, start_segment=start_segment, stop_event=stop_event,
                                  segment_state_path=segment_state_path, segment_dir=segment_dir,
                                  return_report=return_report,
                                  cleanup_on_stop=cleanup_on_stop, keep_segment_dir=keep_segment_dir)


class Client:
    def __init__(self, core: BaseCore = None):
        self.core = core or BaseCore()
        self.core.initialize_session()

    def get_video(self, url: str) -> Video:
        return Video(url, core=self.core)

