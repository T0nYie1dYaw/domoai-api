import enum
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import TypeAdapter

from app.schema import GenModelInfo, MoveModelInfo, VideoModelInfo

current_dir = os.path.dirname(os.path.realpath(__file__))


@lru_cache()
def get_v2v_models() -> List[VideoModelInfo]:
    ta = TypeAdapter(List[VideoModelInfo])
    v2v_models_json_path = os.path.join(current_dir, "models/v2v-models.json")
    with open(v2v_models_json_path, 'r') as f:
        models = ta.validate_json(f.read())
    return models


@lru_cache()
def get_move_models() -> List[MoveModelInfo]:
    ta = TypeAdapter(List[MoveModelInfo])
    v2v_models_json_path = os.path.join(current_dir, "models/move-models.json")
    with open(v2v_models_json_path, 'r') as f:
        models = ta.validate_json(f.read())
    return models


@lru_cache()
def get_gen_models() -> List[GenModelInfo]:
    ta = TypeAdapter(List[GenModelInfo])
    v2v_models_json_path = os.path.join(current_dir, "models/gen-models.json")
    with open(v2v_models_json_path, 'r') as f:
        models = ta.validate_json(f.read())
    return models


@lru_cache()
def get_v2v_model_info_by_instructions(instructions: str) -> Optional[VideoModelInfo]:
    all_model_info = get_v2v_models()
    for model in all_model_info:
        if instructions in model.prompt_args:
            return model
    return None


GenModel = enum.Enum(
    'GenModel',
    {x.name.replace(' ', '_').upper(): x.prompt_args.removeprefix('--') for x in get_gen_models()}
)

MoveModel = enum.Enum(
    'MoveModel',
    {x.name.replace(' ', '_').upper(): x.prompt_args.removeprefix('--') for x in get_move_models()}
)

VideoModel = enum.Enum(
    'VideoModel',
    {x.name.replace(' ', '_').upper(): x.prompt_args.removeprefix('--') for x in get_v2v_models()}
)
