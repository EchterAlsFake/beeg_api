from __future__ import annotations

import copy
import os
import json

from dataclasses import dataclass
from typing import ClassVar
from base_api.modules.type_hints import DownloadReport
from base_api import BaseCore, DownloadConfigHLS, BaseMedia, media_field
from base_api.modules.errors import (
    BotProtectionDetected,
    HTTPStatusError,
    InvalidProxy,
    NetworkRequestError,
    RequestRetriesExhausted,
    UnknownError,
)
from beeg_api.modules.errors import NetworkError, NotFound, UnknownNetworkError, BotDetection, ProxyError, DownloadFailed


async def get_html_content(core: BaseCore, url: str) -> str:
    try:
        return await core.fetch_text(url)

    except HTTPStatusError as e:
        if e.status_code == 404:
            raise NotFound(f"Server returned 404 for: {url}") from e
        raise NetworkError(str(e)) from e

    except (NetworkRequestError, RequestRetriesExhausted) as e:
        raise NetworkError(str(e)) from e

    except InvalidProxy as e:
        raise ProxyError(str(e)) from e

    except BotProtectionDetected as e:
        raise BotDetection(str(e)) from e

    except UnknownError as e:
        raise UnknownNetworkError(str(e)) from e


@dataclass(slots=True, kw_only=True)
class Video(BaseMedia):
    url: str
    core: BaseCore
    title: str | None = media_field("api")
    video_id: str | None = media_field("api")
    duration: int | None = media_field("api")
    m3u8_base_url: str | None = media_field("api")
    key: str | None = media_field("api")

    loader_methods: ClassVar[dict[str, str]] = {"api": "_load_api"}

    async def _load_api(self) -> dict[str, object]:
        """
        Fetches the data from beeg's API and parses it into the dataclass objects
        :return:
        """

        key = self.url.split("/")[-1].strip("-0")

        json_data = await get_html_content(url=f"https://store.externulls.com/facts/file/{key}",
                                                core=self.core)
        json_data = json.loads(json_data)
        # Usually I'd offload to a thread here, but for 50kb of json we don't need the 5 microseconds lol

        file_data = json_data.get("file")
        record = file_data.get("data")[0]
        hls_url = file_data.get("hls_resources").get("fl_cdn_multi")
        return {
            "title": record.get("cd_value"),
            "video_id": record.get("id"),
            "duration": file_data.get("fl_duration"),
            "m3u8_base_url": f"https://video.externulls.com/{hls_url}",
            "key": key,
        }

    async def download(self, configuration: DownloadConfigHLS) -> bool | DownloadReport:
        """
        :param configuration:
        :return:
        """
        await self.load_fields("m3u8_base_url", "title")
        config = copy.deepcopy(configuration)
        config.m3u8_base_url = self.m3u8_base_url
        if not config.no_title:
            config.path = os.path.join(config.path, f"{self.title}.mp4")

        try:
            return await self.core.download(configuration=config)

        except Exception as e:
            raise DownloadFailed(str(e))


class Client:
    def __init__(self, core: BaseCore = BaseCore()):
        self.core = core
        self.core.initialize_session()

    async def get_video(self, url: str, load_api: bool = True):
        video = Video(url=url, core=self.core)
        if load_api:
            await video.load_sources("api")
        return video
