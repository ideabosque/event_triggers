#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bl"

import unittest, sys, logging, os

sys.path.insert(0, "/var/www/projects/event_triggers")

from event_triggers import Cognito
from dotenv import load_dotenv

load_dotenv()

settings = {
    "schema": os.getenv("database_schema"),
    "user": os.getenv("database_username"),
    "password": os.getenv("database_passwd"),
    "host": os.getenv("database_host"),
    "port": os.getenv("database_port"),
    "aws_access_key_id": os.getenv("aws_access_key_id"),
    "aws_secret_access_key": os.getenv("aws_secret_access_key"),
    "aws_region_name": os.getenv("aws_region_name"),
}


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger()


class TriggersTest(unittest.TestCase):
    def setUp(self):
        print(settings)
        self.trigger = Cognito(logger, **settings)

    def tearDown(self):
        pass

    # @unittest.skip("demonstrating skipping")
    def test_pro_token_generate(self):
        event = {
            "version": "1",
            "triggerSource": "TokenGeneration_Authentication",
            "region": "us-west-2",
            "userPoolId": "us-west-2_eOsE8NYle",
            "userName": "barry.y.liu@hotmail.com",
            "callerContext": {
                "awsSdkVersion": "aws-sdk-unknown-unknown",
                "clientId": "156o7tocn7m6aa6ah9tpff9gls",
            },
            "request": {
                "userAttributes": {
                    "sub": "076de22a-6eed-4836-b4bb-ec06f1274311",
                    "cognito:user_status": "CONFIRMED",
                    "email_verified": "true",
                    "email": "barry.y.liu@hotmail.com",
                },
                "groupConfiguration": {
                    "groupsToOverride": [],
                    "iamRolesToOverride": [],
                    "preferredRole": None,
                },
            },
            "response": {"claimsOverrideDetails": None},
        }
        context = {}

        result = self.trigger.pre_token_generate(event, context)
        print(result)


if __name__ == "__main__":
    unittest.main()
