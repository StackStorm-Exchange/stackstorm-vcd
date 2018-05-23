# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and

import json
import yaml

from st2tests.base import BaseActionTestCase


class VCloudBaseActionTestCase(BaseActionTestCase):
    __test__ = False

    def setUp(self):
        super(VCloudBaseActionTestCase, self).setUp()

        self._blank_config = self.load_yaml('cfg_blank.yaml')
        self._good_config = self.load_yaml('cfg_good.yaml')

    def load_yaml(self, filename):
        return yaml.safe_load(self.get_fixture_content(filename))

    def load_json(self, filename):
        return json.loads(self.get_fixture_content(filename))

    @property
    def blank_config(self):
        return self._blank_config

    @property
    def good_config(self):
        return self._good_config

    def test_run_config_blank(self):
        self.assertRaises(ValueError, self.action_cls, self.blank_config)

    def test_run_config_new(self):
        action = self.get_action_instance(self.good_config)
        self.assertIsInstance(action, self.action_cls)
