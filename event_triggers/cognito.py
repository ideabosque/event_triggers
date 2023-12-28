#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, inspect
from .models import SellerModel, TeamModel, UserModel, RelationshipModel
from .enumerations import RoleRelationshipType, SwitchStatus
import json

__author__ = "bl"


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
        # print("Pre generate token::::", event)
        # print(context.__dict__)
        try:
            database_type = self.setting.get("type", "mysql")
            driver_name = self.setting.get("driver", "pymysql")
            charset = self.setting.get("charset", "utf8mb4")
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
                and sources.__contains__(
                    str(event.get("triggerSource")).strip().lower()
                )
                and self.setting.get("user")
                and self.setting.get("password")
                and self.setting.get("host")
                and self.setting.get("port")
                and self.setting.get("schema")
                and event.get("request", {}).get("userAttributes", {}).get("sub")
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
                # print("DATABASE DSN FOR EVENT TRIGGER::::{}".format(dsn))
                session = scoped_session(
                    sessionmaker(
                        autocommit=False,
                        autoflush=False,
                        bind=create_engine(dsn),
                    )
                )
                # 1. Get user
                cognito_user_id = (
                    event.get("request", {}).get("userAttributes", {}).get("sub")
                )
                print("EVENT TRIGGER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", cognito_user_id)
                user = (
                    session.query(UserModel)
                    .filter_by(cognito_user_sub=cognito_user_id)
                    .first()
                )
                claimsToAddOrOverride = {
                    "is_admin": str(SwitchStatus.NO.value),
                    "from": self.setting.get("system_code","ss3"),
                }

                print(
                    "EVENT TRIGGER USER INFO::::::{}".format(
                        {
                            c.key: getattr(user, c.key)
                            for c in inspect(user).mapper.column_attrs
                        }
                    )
                )

                if user:
                    # 1. Attach user id to token.
                    if user.id is not None:
                        claimsToAddOrOverride["user_id"] = str(user.id)

                    # 2. Is admin user
                    if user.is_admin is not None:
                        claimsToAddOrOverride["is_admin"] = str(user.is_admin)

                    # 3. Get seller / teams info
                    if user.seller_id and not user.is_admin:
                        claimsToAddOrOverride["seller_id"] = str(user.seller_id)
                        # 3.1. Get seller info
                        seller = (
                            session.query(SellerModel)
                            .order_by(SellerModel.seller_name.asc())
                            .filter_by(seller_id=user.seller_id)
                        ).first()

                        if seller and seller.s_vendor_id:
                            claimsToAddOrOverride["s_vendor_id"] = str(
                                seller.s_vendor_id
                            )

                        # 3.2. Get teams by seller id
                        permission_filter_conditions = (
                            RelationshipModel.user_id == str(cognito_user_id).strip()
                        ) & (
                            RelationshipModel.type.is_in(
                                RoleRelationshipType.ADMINISTRATOR.value,
                                RoleRelationshipType.COMPANY.value,
                            )
                        )
                        team_filter_conditions = [TeamModel.seller_id == user.seller_id]

                        if user.id is not None:
                            permission_filter_conditions = (
                                permission_filter_conditions
                            ) | (RelationshipModel.user_id == str(user.id).strip())

                        team_ids = list(
                            set(
                                [
                                    relationship.group_id
                                    for relationship in RelationshipModel.scan(
                                        filter_condition=permission_filter_conditions
                                    )
                                    if not relationship.group_id
                                ]
                            )
                        )

                        if len(team_ids):
                            team_filter_conditions.append(
                                TeamModel.team_id.in_(team_ids)
                            )

                        seller_teams = (
                            session.query(TeamModel)
                            .filter(*team_filter_conditions)
                            .all()
                        )
                        teams = {}

                        for team in seller_teams:
                            if team and team.team_id:
                                item = {
                                    "team_id": team.team_id,
                                    "type": team.type,
                                    "vendor_id": team.vendor_id,
                                    "erp_vendor_ref": team.erp_vendor_ref,
                                }

                                teams.update({team.team_id: item})

                        claimsToAddOrOverride.update({"teams": json.dumps(teams)})

                if len(claimsToAddOrOverride.keys()):
                    event["response"]["claimsOverrideDetails"] = {
                        "claimsToAddOrOverride": claimsToAddOrOverride
                    }

                print("Token claims >>>>>>>>>>>>>>>>>>>>", claimsToAddOrOverride)

                session.close()
            # Return to Amazon Cognito
            return event
        except Exception as e:
            print(">>>>>> Pre token generate exception::::", e)
            raise e
        finally:
            return event
