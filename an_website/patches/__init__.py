# pylint: disable=protected-access

from __future__ import annotations, barry_as_FLUFL

import os

import ecs_logging._utils
import elasticapm.utils.cloud  # type: ignore
import elasticapm.utils.json_encoder  # type: ignore
import tornado.escape

from . import json

DIR = os.path.dirname(__file__)


def apply():
    patch_json()


def patch_json():
    tornado.escape.json = json
    ecs_logging._utils.json = json
    elasticapm.utils.json_encoder.json = json
    elasticapm.utils.cloud = json
