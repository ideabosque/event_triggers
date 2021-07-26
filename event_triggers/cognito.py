#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bl"

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from .models import UserModel
from .models import TeamUserModel
from .models import RoleModel


# {
#     "version": "1",
#     "triggerSource": "TokenGeneration_Authentication",
#     "region": "us-west-2",
#     "userPoolId": "us-west-2_eOsE8NYle",
#     "userName": "barry.y.liu@hotmail.com",
#     "callerContext": {
#         "awsSdkVersion": "aws-sdk-unknown-unknown",
#         "clientId": "156o7tocn7m6aa6ah9tpff9gls",
#     },
#     "request": {
#         "userAttributes": {
#             "sub": "f2b3a074-eb9e-4210-81b2-cbe617ecc50b",
#             "cognito:user_status": "CONFIRMED",
#             "email_verified": "true",
#             "email": "barry.y.liu@hotmail.com",
#         },
#         "groupConfiguration": {
#             "groupsToOverride": [],
#             "iamRolesToOverride": [],
#             "preferredRole": None,
#         },
#     },
#     "response": {"claimsOverrideDetails": None},
# }


class Cognito(object):
    def __init__(self, logger, **settings):
        self.logger = logger
        self.setting = settings

    # Trigger of pre-generate token
    def pre_token_generate(self, event, context):
        database_type = (
            self.setting.get("type") if self.setting.get("type") else "mysql"
        )
        driver_name = (
            self.setting.get("driver") if self.setting.get("driver") else "pymysql"
        )
        charset = (
            self.setting.get("charset") if self.setting.get("charset") else "utf8mb4"
        )
        sources = [
            "tokengeneration_hostedauth",
            "tokengeneration_newpasswordchallenge",
            "tokengeneration_authenticatedevice",
            "tokengeneration_refreshtokens",
            "tokengeneration_authentication",
        ]

        if (
            event
            and event.get("triggerSource")
            and sources.__contains__(event.get("triggerSource").lower())
            and self.setting.get("user")
            and self.setting.get("password")
            and self.setting.get("host")
            and self.setting.get("port")
            and self.setting.get("schema")
            and event.get("request").get("userAttributes").get("sub")
        ):
            dsn = "{}+{}://{}:{}@{}:{}/{}?charset={}".format(
                database_type,
                driver_name,
                self.setting.get("user"),
                self.setting.get("password"),
                self.setting.get("host"),
                self.setting.get("port"),
                self.setting.get("schema"),
                charset,
            )
            engine = create_engine(dsn)
            session = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=engine)
            )

            # 1. Get seller_id
            cognito_user_id = event.get("request").get("userAttributes").get("sub")
            user = (
                session.query(UserModel)
                .filter_by(cognito_user_sub=cognito_user_id)
                .first()
            )

            if hasattr(user, "seller_id"):
                # 2. Get team id
                team_user_relation = (
                    session.query(TeamUserModel).filter_by(user_id=user.id).first()
                )

                # 3. Get role id
                # role_ids = []
                # role_names = []
                # roles = RoleModel.scan(RoleModel.user_ids.contains(cognito_user_id))

                # for role in roles:
                #     role_ids.append(role.role_id)
                #     role_names.append(role.name)

                event["response"]["claimsOverrideDetails"] = {
                    "claimsToAddOrOverride": {
                        "seller_id": str(user.seller_id),
                        "team_id": str(team_user_relation.team_id)
                        if hasattr(team_user_relation, "team_id")
                        else "",
                        "vendor_id": str(team_user_relation.team.vendor_id)
                        if hasattr(team_user_relation, "team")
                        and hasattr(team_user_relation.team, "vendor_id")
                        else "",
                        "is_admin": str(user.is_admin),
                        "user_id": str(user.id),
                        "s_vendor_id": str(user.s_vendor_id),
                        # "role_id": ",".join(role_ids),
                        # "roles": ",".join(role_names),
                    }
                }

            session.close()

        # Return to Amazon Cognito
        return event
