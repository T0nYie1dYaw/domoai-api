import json
import os

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

current_dir = os.path.dirname(os.path.realpath(__file__))


class ScriptSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(current_dir, '../.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )
    domoai_web_token: str


def update_models(req_end_path: str, filename: str, web_token: str):
    res = httpx.get(f'https://api.domoai.app/web-post/model/{req_end_path}?offset=0&limit=100&locale=en', headers={
        'Authorization': f'Bearer {web_token}'
    })

    models = res.json()['data']['models']
    with open(os.path.join(current_dir, f'../app/models/{filename}.json'), 'w') as f:
        json.dump(models, f)


if __name__ == '__main__':
    settings = ScriptSettings()

    update_models(req_end_path='video-models', filename='v2v-models', web_token=settings.domoai_web_token)
    update_models(req_end_path='gen-models', filename='gen-models', web_token=settings.domoai_web_token)
    update_models(req_end_path='move-models', filename='move-models', web_token=settings.domoai_web_token)
