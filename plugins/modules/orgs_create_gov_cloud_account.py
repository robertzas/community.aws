#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: sts_assume_role
version_added: 1.0.0
short_description: Assume a role using AWS Security Token Service and obtain temporary credentials
description:
    - Assume a role using AWS Security Token Service and obtain temporary credentials.
author:
    - Boris Ekelchik (@bekelchik)
    - Marek Piatek (@piontas)
options:
  role_arn:
    description:
      - The Amazon Resource Name (ARN) of the role that the caller is
        assuming U(https://docs.aws.amazon.com/IAM/latest/UserGuide/Using_Identifiers.html#Identifiers_ARNs).
    required: true
    type: str
  role_session_name:
    description:
      - Name of the role's session - will be used by CloudTrail.
    required: true
    type: str
  policy:
    description:
      - Supplemental policy to use in addition to assumed role's policies.
    type: str
  duration_seconds:
    description:
      - The duration, in seconds, of the role session. The value can range from 900 seconds (15 minutes) to 43200 seconds (12 hours).
      - The max depends on the IAM role's sessions duration setting.
      - By default, the value is set to 3600 seconds.
    type: int
  external_id:
    description:
      - A unique identifier that is used by third parties to assume a role in their customers' accounts.
    type: str
  mfa_serial_number:
    description:
      - The identification number of the MFA device that is associated with the user who is making the AssumeRole call.
    type: str
  mfa_token:
    description:
      - The value provided by the MFA device, if the trust policy of the role being assumed requires MFA.
    type: str
notes:
  - In order to use the assumed role in a following playbook task you must pass the access_key, access_secret and access_token.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
"""

RETURN = """
sts_creds:
    description: The temporary security credentials, which include an access key ID, a secret access key, and a security (or session) token
    returned: always
    type: dict
    sample:
      access_key: XXXXXXXXXXXXXXXXXXXX
      expiration: '2017-11-11T11:11:11+00:00'
      secret_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      session_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
sts_user:
    description: The Amazon Resource Name (ARN) and the assumed role ID
    returned: always
    type: dict
    sample:
      assumed_role_id: arn:aws:sts::123456789012:assumed-role/demo/Bob
      arn: ARO123EXAMPLE123:Bob
changed:
    description: True if obtaining the credentials succeeds
    type: bool
    returned: always
"""

EXAMPLES = """
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Assume an existing role (more details: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- community.aws.sts_assume_role:
    role_arn: "arn:aws:iam::123456789012:role/someRole"
    role_session_name: "someRoleSession"
  register: assumed_role

# Use the assumed role above to tag an instance in account 123456789012
- amazon.aws.ec2_tag:
    aws_access_key: "{{ assumed_role.sts_creds.access_key }}"
    aws_secret_key: "{{ assumed_role.sts_creds.secret_key }}"
    security_token: "{{ assumed_role.sts_creds.session_token }}"
    resource: i-xyzxyz01
    state: present
    tags:
      MyNewTag: value

"""

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (
    camel_dict_to_snake_dict,
)


def _parse_response(response):
    create_account_status = response.get("CreateAccountStatus", {})
    return camel_dict_to_snake_dict(create_account_status)


def create_gov_cloud_account(connection, module):
    params = {
        "Email": module.params.get("email"),
        "AccountName": module.params.get("account_name"),
        "RoleName": module.params.get("role_name"),
        "IamUserAccessToBilling": module.params.get("iam_user_access_to_billing"),
        "Tags": module.params.get("tags"),
        "CreateAccountRequestId": module.params.get("create_account_request_id"),
    }
    changed = False

    kwargs = dict((k, v) for k, v in params.items() if v is not None)

    try:
        if "CreateAccountRequestId" in kwargs:
            response = connection.describe_create_account_status(**kwargs)
        else:
            response = connection.create_gov_cloud_account(**kwargs)
            changed = True
    except Exception as e:
        module.fail_json_aws(e)

    create_account_status = _parse_response(response)

    if create_account_status.get("state") == "FAILED":
        module.fail_json_aws(create_account_status)

    module.exit_json(changed=changed, **create_account_status)


def main():
    argument_spec = dict(
        email=dict(default=None),
        account_name=dict(default=None),
        role_name=dict(default=None),
        iam_user_access_to_billing=dict(default=None),
        tags=dict(default=None),
        create_account_request_id=dict(default=None),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        # supports_check_mode=True
    )

    connection = module.client("organizations")

    create_gov_cloud_account(connection, module)


if __name__ == "__main__":
    main()
