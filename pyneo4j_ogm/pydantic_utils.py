"""
Pydantic compatibility utility module.
"""

from typing import Any, Type, Union

import pydantic
from pydantic import BaseModel

IS_PYDANTIC_V2 = int(pydantic.VERSION.split(".", maxsplit=1)[0]) >= 2

if IS_PYDANTIC_V2:
    from pydantic import TypeAdapter
else:
    from pydantic import parse_obj_as


def parse_object_as(object_type: Type, data: Any):
    if IS_PYDANTIC_V2:
        return TypeAdapter(object_type).validate_python(data)
    else:
        return parse_obj_as(object_type, data)


def get_field_type(field):
    if IS_PYDANTIC_V2:
        return field.annotation
    else:
        return field.outer_type_


def get_model_fields(model):
    if IS_PYDANTIC_V2:
        return model.model_fields
    else:
        return model.__fields__


def parse_model(model_type, data: Any):
    if IS_PYDANTIC_V2:
        return model_type.model_validate(data)
    else:
        return model_type.parse_obj(data)


def get_extra_field_info(field, parameter: str):
    if IS_PYDANTIC_V2:
        if field.json_schema_extra is not None:
            return field.json_schema_extra.get(parameter)
        return None
    else:
        return field.field_info.extra.get(parameter)


def get_config_value(model, parameter: str):
    if IS_PYDANTIC_V2:
        return model.model_config.get(parameter)
    else:
        return getattr(model.Config, parameter, None)


def get_model_dump(model: BaseModel, *args, **kwargs):
    if IS_PYDANTIC_V2:
        return model.model_dump(*args, **kwargs)
    else:
        return model.dict(*args, **kwargs)


def get_model_dump_json(model: BaseModel, *args, **kwargs):
    if IS_PYDANTIC_V2:
        return model.model_dump_json(*args, **kwargs)
    else:
        return model.json(*args, **kwargs)


def get_schema(model: Union[BaseModel, Type[BaseModel]], *args, **kwargs):
    if IS_PYDANTIC_V2:
        return model.model_json_schema(*args, **kwargs)
    else:
        return model.schema(*args, **kwargs)
