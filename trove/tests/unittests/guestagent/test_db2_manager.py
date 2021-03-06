# Copyright 2015 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import testtools
from mock import MagicMock
from mock import patch
from testtools.matchers import Is, Equals, Not
from trove.common.context import TroveContext
from trove.common.instance import ServiceStatuses
from trove.guestagent import volume
from trove.guestagent.datastore.experimental.db2 import (
    service as db2_service)
from trove.guestagent.datastore.experimental.db2 import (
    manager as db2_manager)
from trove.guestagent import pkg as pkg


class GuestAgentDB2ManagerTest(testtools.TestCase):

    def setUp(self):
        super(GuestAgentDB2ManagerTest, self).setUp()
        self.real_status = db2_service.DB2AppStatus.set_status

        class FakeInstanceServiceStatus(object):
            status = ServiceStatuses.NEW

            def save(self):
                pass

        db2_service.DB2AppStatus.set_status = MagicMock(
            return_value=FakeInstanceServiceStatus())
        self.context = TroveContext()
        self.manager = db2_manager.Manager()
        self.real_db_app_status = db2_service.DB2AppStatus
        self.origin_format = volume.VolumeDevice.format
        self.origin_mount = volume.VolumeDevice.mount
        self.origin_mount_points = volume.VolumeDevice.mount_points
        self.origin_stop_db = db2_service.DB2App.stop_db
        self.origin_start_db = db2_service.DB2App.start_db
        self.orig_change_ownership = (db2_service.DB2App.change_ownership)
        self.orig_create_databases = db2_service.DB2Admin.create_database
        self.orig_list_databases = db2_service.DB2Admin.list_databases
        self.orig_delete_database = db2_service.DB2Admin.delete_database
        self.orig_create_users = db2_service.DB2Admin.create_user
        self.orig_list_users = db2_service.DB2Admin.list_users
        self.orig_delete_user = db2_service.DB2Admin.delete_user

    def tearDown(self):
        super(GuestAgentDB2ManagerTest, self).tearDown()
        db2_service.DB2AppStatus.set_status = self.real_db_app_status
        volume.VolumeDevice.format = self.origin_format
        volume.VolumeDevice.mount = self.origin_mount
        volume.VolumeDevice.mount_points = self.origin_mount_points
        db2_service.DB2App.stop_db = self.origin_stop_db
        db2_service.DB2App.start_db = self.origin_start_db
        db2_service.DB2App.change_ownership = self.orig_change_ownership
        db2_service.DB2Admin.create_database = self.orig_create_databases
        db2_service.DB2Admin.create_user = self.orig_create_users
        db2_service.DB2Admin.create_database = self.orig_create_databases
        db2_service.DB2Admin.list_databases = self.orig_list_databases
        db2_service.DB2Admin.delete_database = self.orig_delete_database
        db2_service.DB2Admin.create_user = self.orig_create_users
        db2_service.DB2Admin.list_users = self.orig_list_users
        db2_service.DB2Admin.delete_user = self.orig_delete_user

    def test_update_status(self):
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        self.manager.update_status(self.context)
        mock_status.update.assert_any_call()

    def test_prepare_device_path_true(self):
        self._prepare_dynamic()

    def test_prepare_device_path_false(self):
        self._prepare_dynamic(device_path=None)

    def test_prepare_database(self):
        self._prepare_dynamic(databases=['db1'])

    def _prepare_dynamic(self, packages=None, databases=None, users=None,
                         config_content=None, device_path='/dev/vdb',
                         is_db_installed=True, backup_id=None, overrides=None):
        mock_status = MagicMock()
        mock_app = MagicMock()
        self.manager.appStatus = mock_status
        self.manager.app = mock_app

        mock_status.begin_install = MagicMock(return_value=None)
        pkg.Package.pkg_is_installed = MagicMock(return_value=is_db_installed)
        mock_app.change_ownership = MagicMock(return_value=None)
        mock_app.restart = MagicMock(return_value=None)
        mock_app.start_db = MagicMock(return_value=None)
        mock_app.stop_db = MagicMock(return_value=None)
        volume.VolumeDevice.format = MagicMock(return_value=None)
        volume.VolumeDevice.mount = MagicMock(return_value=None)
        volume.VolumeDevice.mount_points = MagicMock(return_value=[])
        db2_service.DB2Admin.create_user = MagicMock(return_value=None)
        db2_service.DB2Admin.create_database = MagicMock(return_value=None)

        self.manager.prepare(context=self.context, packages=packages,
                             config_contents=config_content,
                             databases=databases,
                             memory_mb='2048', users=users,
                             device_path=device_path,
                             mount_point="/home/db2inst1/db2inst1",
                             backup_info=None,
                             overrides=None,
                             cluster_config=None)
        mock_status.begin_install.assert_any_call()
        self.assertEqual(1, mock_app.change_ownership.call_count)
        if databases:
            self.assertTrue(db2_service.DB2Admin.create_database.called)
        else:
            self.assertFalse(db2_service.DB2Admin.create_database.called)

        if users:
            self.assertTrue(db2_service.DB2Admin.create_user.called)
        else:
            self.assertFalse(db2_service.DB2Admin.create_user.called)

    def test_restart(self):
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        with patch.object(db2_service.DB2App, 'restart',
                          return_value=None) as restart_mock:
            #invocation
            self.manager.restart(self.context)
            #verification/assertion
            restart_mock.assert_any_call()

    def test_stop_db(self):
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2App.stop_db = MagicMock(return_value=None)
        self.manager.stop_db(self.context)
        db2_service.DB2App.stop_db.assert_any_call(
            do_not_start_on_reboot=False)

    def test_create_database(self):
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2Admin.create_database = MagicMock(return_value=None)
        self.manager.create_database(self.context, ['db1'])
        db2_service.DB2Admin.create_database.assert_any_call(['db1'])

    def test_create_user(self):
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2Admin.create_user = MagicMock(return_value=None)
        self.manager.create_user(self.context, ['user1'])
        db2_service.DB2Admin.create_user.assert_any_call(['user1'])

    def test_delete_database(self):
        databases = ['db1']
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2Admin.delete_database = MagicMock(return_value=None)
        self.manager.delete_database(self.context, databases)
        db2_service.DB2Admin.delete_database.assert_any_call(databases)

    def test_delete_user(self):
        user = ['user1']
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2Admin.delete_user = MagicMock(return_value=None)
        self.manager.delete_user(self.context, user)
        db2_service.DB2Admin.delete_user.assert_any_call(user)

    def test_list_databases(self):
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2Admin.list_databases = MagicMock(
            return_value=['database1'])
        databases = self.manager.list_databases(self.context)
        self.assertThat(databases, Not(Is(None)))
        self.assertThat(databases, Equals(['database1']))
        db2_service.DB2Admin.list_databases.assert_any_call(None, None, False)

    def test_list_users(self):
        db2_service.DB2Admin.list_users = MagicMock(return_value=['user1'])
        users = self.manager.list_users(self.context)
        self.assertThat(users, Equals(['user1']))
        db2_service.DB2Admin.list_users.assert_any_call(None, None, False)

    def test_get_users(self):
        username = ['user1']
        hostname = ['host']
        mock_status = MagicMock()
        self.manager.appStatus = mock_status
        db2_service.DB2Admin.get_user = MagicMock(return_value=['user1'])
        users = self.manager.get_user(self.context, username, hostname)
        self.assertThat(users, Equals(['user1']))
        db2_service.DB2Admin.get_user.assert_any_call(username, hostname)

    def test_reset_configuration(self):
        try:
            configuration = {'config_contents': 'some junk'}
            self.manager.reset_configuration(self.context, configuration)
        except Exception:
            self.fail("reset_configuration raised exception unexpectedly.")

    def test_rpc_ping(self):
        output = self.manager.rpc_ping(self.context)
        self.assertTrue(output)
