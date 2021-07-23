#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bl"

import os, pendulum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func, Text, Table
from pynamodb.models import Model
from pynamodb.attributes import (
    ListAttribute,
    MapAttribute,
    UnicodeAttribute,
    BooleanAttribute,
    UTCDateTimeAttribute,
)

Base = declarative_base()


class BaseModel(Model):
    class Meta:
        billing_mode = "PAY_PER_REQUEST"
        region = os.getenv("REGIONNAME")
        aws_access_key_id = os.getenv("aws_access_key_id")
        aws_secret_access_key = os.getenv("aws_secret_access_key")

        if region is None or aws_access_key_id is None or aws_secret_access_key is None:
            from dotenv import load_dotenv

            if load_dotenv():
                if region is None:
                    region = os.getenv("region_name")

                if aws_access_key_id is None:
                    aws_access_key_id = os.getenv("aws_access_key_id")

                if aws_secret_access_key is None:
                    aws_secret_access_key = os.getenv("aws_secret_access_key")


class TraitModel(BaseModel):
    class Meta(BaseModel.Meta):
        pass

    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()
    updated_by = UnicodeAttribute()


class RoleModel(TraitModel):
    class Meta(TraitModel.Meta):
        table_name = "se-roles"

    role_id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    permissions = ListAttribute(of=MapAttribute)
    description = UnicodeAttribute()
    is_admin = BooleanAttribute()
    user_ids = ListAttribute()


class TeamUserModel(Base):
    __tablename__ = "team_users"
    team_user_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    # team = relationship("TeamModel", backref="user_teams")
    # user = relationship("UserModel", backref="team_users")


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    created_at = Column(
        DateTime, default=pendulum.now(tz="UTC").format("YYYY-MM-DD hh:mm:ss")
    )
    updated_at = Column(
        DateTime, default=pendulum.now(tz="UTC").format("YYYY-MM-DD hh:mm:ss")
    )
    is_active = Column(Integer)
    is_admin = Column(Integer)
    ns_internal_id = Column(Integer)
    lang_code = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    title = Column(String)
    phone = Column(String)
    ext = Column(String)
    locale_code = Column(String)
    seller_id = Column(Integer)
    erp_employee_ref = Column(Integer)
    cognito_user_sub = Column(String)
    # sellers = relationship(
    #     "SellerManagerModel", back_populates="manager"
    # )
