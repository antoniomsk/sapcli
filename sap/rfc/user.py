"""User management over RFC"""

import datetime

from typing import Dict, Union, List

from sap.rfc.core import RFCParams
from sap.rfc.bapi import BAPIError


UserId = str
UserAddress = Dict[str, str]


def add_to_dict_if_not_none(target_dict, target_key, value):
    """Adds the given value to the give dict as the given key
       only if the given value is not None.
    """

    if value is None:
        return False

    target_dict[target_key] = value
    return True


def add_to_dict_if_not_present(target_dict, target_key, value):
    """Adds the given value to the give dict as the given key
       only if the given key is not in the given dict yet.
    """

    if target_key in target_dict:
        return False

    target_dict[target_key] = value
    return True


def sap_date_from(the_date):
    return the_date.strftime('%Y%m%d')


def today_sap_date():
    return sap_date_from(datetime.date.today())


class UserBuilder:
    """An utility class for building SAP user parameters"""

    def __init__(self):
        self._username = None
        self._address = None
        self._logondata = None
        self._password = None
        self._alias = None

    @property
    def _address_data(self) -> UserAddress:
        if self._address is None:
            self._address = {}

        return self._address

    @property
    def _password_data(self) -> Dict[str, str]:
        if self._password is None:
            self._password = {}

        return self._password

    @property
    def _alias_data(self) -> Dict[str, str]:
        if self._alias is None:
            self._alias = {}

        return self._alias

    @property
    def _logondata_data(self) -> Dict[str, str]:
        if self._logondata is None:
            self._logondata = {}

        return self._logondata

    def set_username(self, username: str):
        """Sets user name for logon"""

        self._username = username
        return self

    def set_first_name(self, first_name: str):
        """Sets user's first name"""

        self._address_data['FIRSTNAME'] = first_name
        return self

    def set_last_name(self, last_name: str):
        """Sets user's last name"""

        self._address_data['LASTNAME'] = last_name
        return self

    def set_email_address(self, email_address: str):
        """Sets user's email address"""

        self._address['E_MAIL'] = email_address
        return self

    def set_password(self, password: str):
        """Sets user's password - works only for the user type Service"""

        self._password_data['BAPIPWD'] = password
        return self

    def set_alias(self, alias: str):
        """Sets user's alias for HTTP authentication"""

        self._alias_data['USERALIAS'] = alias
        return self

    def set_type(self, typ: str):
        """Sets user's type"""

        self._logondata_data['USTYP'] = typ
        return self

    def set_valid_from(self, start_date: Union[str]):
        """Sets user's start validity date"""

        if isinstance(start_date, str):
            self._logondata_data['GLTGV'] = start_date
        else:
            raise ValueError()

        return self

    def set_valid_to(self, end_date: Union[str]):
        """Sets user's end validity date"""

        if isinstance(end_date, str):
            self._logondata_data['GLTGB'] = end_date
        else:
            raise ValueError()

        return self

    def build_rfc_params(self) -> RFCParams:
        """Creates RFC parameters"""

        params = dict()

        add_to_dict_if_not_none(params, 'USERNAME', self._username)
        add_to_dict_if_not_none(params, 'ADDRESS', self._address)
        add_to_dict_if_not_none(params, 'PASSWORD', self._password)
        add_to_dict_if_not_none(params, 'ALIAS', self._alias)

        add_to_dict_if_not_present(self._logondata_data, 'GLTGV', today_sap_date())
        add_to_dict_if_not_present(self._logondata_data, 'GLTGB', '20991231')

        add_to_dict_if_not_none(params, 'LOGONDATA', self._logondata)

        return params


class UserRoleAssignmentBuilder:
    """An utility class for building SAP user roles assignment parameters"""

    def __init__(self, user):
        self._user = user
        self._roles = list()

    def add_roles(self, role_names: List[str]):
        """Set assigned roles name"""

        self._roles = role_names
        return self

    def build_rfc_params(self) -> RFCParams:
        """Creates RFC parameters"""

        if not self._roles:
            return None

        rfc_table = []

        for role_name in self._roles:
            table_row = {'AGR_NAME': role_name}

            add_to_dict_if_not_present(table_row, 'FROM_DAT', today_sap_date())
            add_to_dict_if_not_present(table_row, 'TO_DAT', '20991231')

            rfc_table.append(table_row)

        return {
            'USERNAME': self._user,
            'ACTIVITYGROUPS': rfc_table
        }


class UserProfileAssignmentBuilder:
    """An utility class for building SAP user profiles assignment parameters"""

    def __init__(self, user):
        self._user = user
        self._profiles = list()

    def add_profiles(self, profile_names: List[str]):
        """Set assigned profiles name"""

        self._profiles = profiles
        return self

    def build_rfc_params(self) -> RFCParams:
        """Creates RFC parameters"""

        if not self._profiles:
            return None

        rfc_table = []

        for profile_name in self._profiles:
            table_row = {'BAPIPROF': profile_name}
            rfc_table.append(table_row)

        return {
            'USERNAME': self._user,
            'PROFILES': rfc_table
        }


class UserManager:
    """Proxy to SAP API managing Users"""

    def __init__(self, conn):
        self._conn = conn

    def user_builder() -> UserBuilder:
        """Returns instance of User Parameters builder"""

        return UserBuilder()

    def create_user(self, user_builder: UserBuilder) -> UserId:
        """Creates a new user for the given user data"""

        rfc_call_params = user_builder.build_rfc_params()

        resp = conn.call('BAPI_USER_CREATE1', **rfc_call_params)

        BAPIError.raise_for_error(resp['RETURN'])

        return rfc_call_params['USERNAME']

    def user_role_assignment_builder() -> UserRoleAssignmentBuilder:
        """Returns instance of User Role Assignment builder"""

        return UserRoleAssignmentBuilder()

    def assign_roles(self, roles_builder: UserRoleAssignmentBuilder) -> None:
        """Assigns roles"""

        rfc_call_params = roles_builder.build_rfc_params()

        resp = conn.call('BAPI_USER_ACTGROUPS_ASSIGN', **rfc_call_params)

        BAPIError.raise_for_error(resp['RETURN'])

    def user_profile_assignment_builder() -> UserProfileAssignmentBuilder:
        """Returns instance of User Profile Assignment builder"""

        return UserProfileAssignmentBuilder()

    def assign_profiles(self, profiles_builder: UserProfileAssignmentBuilder) -> None:
        """Assigns profiles"""

        rfc_call_params = profiles_builder.build_rfc_params()

        resp = conn.call('BAPI_USER_PROFILES_ASSIGN', **rfc_call_params)

        BAPIError.raise_for_error(resp['RETURN'])
