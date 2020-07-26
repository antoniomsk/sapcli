#!/usr/bin/env python3

import datetime

import unittest
from unittest.mock import Mock

from sap.rfc.bapi import BAPIError
from sap.rfc.user import add_to_dict_if_not_none, add_to_dict_if_not_present, today_sap_date, \
         UserBuilder, UserRoleAssignmentBuilder, UserProfileAssignmentBuilder, UserManager

from test_sap_rfc_bapi import create_bapiret_error


class SAPRFCUserAux(unittest.TestCase):

    def test_add_to_dict_if_not_none_none(self):
        target = dict()

        ret = add_to_dict_if_not_none(target, 'key', None)

        self.assertNotIn('key', target)
        self.assertFalse(ret)

    def test_add_to_dict_if_not_none_not_none(self):
        target = dict()

        ret = add_to_dict_if_not_none(target, 'key', 'value')

        self.assertIn('key', target)
        self.assertEqual(target, {'key': 'value'})
        self.assertTrue(ret)

    def test_add_to_dict_if_not_present_yes(self):
        target = dict()

        ret = add_to_dict_if_not_present(target, 'key', 'value')

        self.assertIn('key', target)
        self.assertEqual(target, {'key': 'value'})
        self.assertTrue(ret)

    def test_add_to_dict_if_not_present_no(self):
        target = {'key': 'value'}

        ret = add_to_dict_if_not_present(target, 'key', 'foo')

        self.assertIn('key', target)
        self.assertEqual(target, {'key': 'value'})
        self.assertFalse(ret)

class TestUserBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = UserBuilder()

    def test_no_parameters_provided(self):
        params = self.builder.build_rfc_params()

        date = datetime.date.today().strftime('%Y%m%d')

        self.assertEqual(params, {'LOGONDATA': {'GLTGV': date, 'GLTGB': '20991231'}})

    def test_all_parameters_provided(self):
        username = 'FOO'
        first_name = 'First'
        last_name = 'Last'
        email_address = 'email@example.org'
        password = 'Password'
        alias = 'HTTP_ALIAS'
        typ = 'S'
        start_date = '20200101'
        end_date = '20201231'

        self.builder\
            .set_username(username)\
            .set_first_name(first_name)\
            .set_last_name(last_name)\
            .set_email_address(email_address)\
            .set_password(password)\
            .set_alias(alias)\
            .set_type(typ)\
            .set_valid_from(start_date)\
            .set_valid_to(end_date)

        params = self.builder.build_rfc_params()

        self.assertEqual(params, {
            'USERNAME': username,
            'ALIAS': {
                'USERALIAS': alias
            },
            'ADDRESS': {
                'FIRSTNAME': first_name,
                'LASTNAME': last_name,
                'E_MAIL': email_address
            },
            'PASSWORD': {
                'BAPIPWD': password
            },
            'LOGONDATA': {
                'USTYP': typ,
                'GLTGV': start_date,
                'GLTGB': end_date
            }
        })


class TestUserRoleAssignmentBuilder(unittest.TestCase):

    def setUp(self):
        self.username = 'LOGON'
        self.builder = UserRoleAssignmentBuilder(self.username)

    def test_no_parameters_provided(self):
        params = self.builder.build_rfc_params()
        self.assertIsNone(params)

    def test_all_parameters_provided(self):
        self.builder.add_roles(['1', '2', '3'])

        params = self.builder.build_rfc_params()

        start_date = today_sap_date()
        self.maxDiff = None
        self.assertEqual(params, {
            'USERNAME': self.username,
            'ACTIVITYGROUPS': [
                {'AGR_NAME': '1',
                 'FROM_DAT': start_date,
                 'TO_DAT': '20991231'
                },
                {'AGR_NAME': '2',
                 'FROM_DAT': start_date,
                 'TO_DAT': '20991231'
                },
                {'AGR_NAME': '3',
                 'FROM_DAT': start_date,
                 'TO_DAT': '20991231'
                }
            ]
        })


class TestUserProfileAssignmentBuilder(unittest.TestCase):

    def setUp(self):
        self.username = 'LOGON'
        self.builder = UserProfileAssignmentBuilder(self.username)

    def test_no_parameters_provided(self):
        params = self.builder.build_rfc_params()
        self.assertIsNone(params)

    def test_all_parameters_provided(self):
        self.builder.add_profiles(['1', '2', '3'])

        params = self.builder.build_rfc_params()

        start_date = today_sap_date()
        self.maxDiff = None
        self.assertEqual(params, {
            'USERNAME': self.username,
            'PROFILES': [
                {'BAPIPROF': '1',
                },
                {'BAPIPROF': '2',
                },
                {'BAPIPROF': '3',
                }
            ]
        })


class TestUserManager(unittest.TestCase):

    def setUp(self):
        self.bapirettab = []
        self.response = {'RETURN': self.bapirettab}

        self.connection = Mock()
        self.connection.call = Mock()
        self.connection.call.return_value = self.response

        self.username = 'logon'
        self.manager = UserManager()

    def test_user_builder(self):
        self.assertIsNotNone(self.manager.user_builder())

    def test_user_role_assignment_builder(self):
        builder = self.manager.user_role_assignment_builder(self.username)
        self.assertIsNotNone(builder)
        self.assertEqual(builder._user, self.username)

    def test_user_profile_assignment_builder(self):
        builder = self.manager.user_profile_assignment_builder(self.username)
        self.assertIsNotNone(builder)
        self.assertEqual(builder._user, self.username)

    def test_create_user_no_error(self):
        user_builder = self.manager.user_builder()
        user_builder.set_username(self.username)

        ret = self.manager.create_user(self.connection, user_builder)

        self.assertEqual(ret, self.username)

        self.connection.call.assert_called_once()

    def test_create_user_with_error(self):
        user_builder = self.manager.user_builder()
        user_builder.set_username(self.username)

        self.bapirettab.append(create_bapiret_error('Error message'))

        with self.assertRaises(BAPIError) as caught:
            self.manager.create_user(self.connection, user_builder)

        self.connection.call.assert_called_once()
