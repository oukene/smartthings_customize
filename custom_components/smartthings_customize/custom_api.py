import logging
import aiohttp
import json
from homeassistant.util import ssl
import traceback

import json
import os

from pysmartthings import App

import traceback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

BASE = "custom_components/" + DOMAIN + "/"

async def async_remove_app_info(app_id):
    try:
        path = BASE + app_id + ".json"
        os.remove(path)
    except:
        """"""

async def async_get_app_info(hass, app_id, token):

    path = BASE + app_id + ".json"

    app = App()
    try:
        # 파일이 있는지 먼저 확인
        if os.path.isfile(path):
            def load():
                with open(path, "r") as f:
                    data = json.load(f)
                    app.apply_data(data)
                return app
            app = await hass.async_add_executor_job(load)
            return app
        else:
            url = "https://api.smartthings.com/v1/apps/" + app_id
            custom_ssl_context = ssl.get_default_context()
            custom_ssl_context.options |= 0x00040000
            headers={"Authorization": "Bearer " + token}

            connector = aiohttp.TCPConnector(ssl=custom_ssl_context)
            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        raw_data = await response.read()
                        data = json.loads(raw_data)
                        app.apply_data(data)
                        def save(data):
                            with open(path, "w") as f:
                                json.dump(obj=data, fp=f, sort_keys=True, indent=4)
                        await hass.async_add_executor_job(save, data)
                        return app

    except Exception as e:
        _LOGGER.error("get_app_info failed - " + traceback.format_exc())

        
