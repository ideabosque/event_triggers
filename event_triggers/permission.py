#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from silvaengine_utility import Utility
from .enumerations import SwitchStatus

__author__ = "bl"


class Permission(object):
    def __init__(self, logger, **settings):
        self.logger = logger
        self.setting = settings

    # Implementation of hook configuration `after_token_parsed_hooks`
    @staticmethod
    def after_token_parsed_ss3(claims, context):
        try:
            is_admin = int(str(claims.get("is_admin", SwitchStatus.NO.value)).strip())

            # Use `endpoint_id` to differentiate app channels
            if bool(is_admin) == False:
                owner_id = claims.get("seller_id")
                teams = claims.get("teams")

                if not context.get("seller_id") or not context.get("team_id"):
                    raise Exception("Missing required parameter(s)", 400)
                elif str(owner_id).strip() != context.get("seller_id"):
                    raise Exception("Access exceeded", 403)
                elif teams:
                    teams = dict(**Utility.json_loads(str(teams).strip()))

                    if teams.get(context.get("team_id")) is None:
                        raise Exception("Access exceeded", 403)

                    claims.pop("teams")
                    claims.update(teams.get(context.get("team_id")))
            print("Only work for ss3 ..........................", claims)
            return claims
        except Exception as e:
            raise e
