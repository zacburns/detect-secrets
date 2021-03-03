import re

import requests

from .base import RegexBasedDetector
from detect_secrets.core.constants import VerifiedResult


class CloudantDetector(RegexBasedDetector):
    """ Scans for Cloudant Credentials """

    secret_type = 'Cloudant Credentials'

    # opt means optional
    dot = r'\.'
    cl_account = r'[\w\-]+'
    cl = r'(?:cloudant|cl|clou)'
    opt_api = r'(?:api|)'
    cl_key_or_pass = opt_api + r'(?:key|pwd|pw|password|pass|token|creds|credentials|cred)'
    cl_pw = r'([0-9a-f]{64})'
    cl_api_key = r'([a-z]{24})'
    colon = r'\:'
    at = r'\@'
    http = r'(?:https?\:\/\/)'
    cloudant_api_url = r'cloudant\.com'
    denylist = [
        RegexBasedDetector.assign_regex_generator(
            prefix_regex=cl,
            password_keyword_regex=cl_key_or_pass,
            password_regex=cl_pw,
        ),
        RegexBasedDetector.assign_regex_generator(
            prefix_regex=cl,
            password_keyword_regex=cl_key_or_pass,
            password_regex=cl_api_key,
        ),
        re.compile(
            r'{http}{cl_account}{colon}{cl_pw}{at}{cl_account}{dot}{cloudant_api_url}'.format(
                http=http,
                colon=colon,
                cl_account=cl_account,
                cl_pw=cl_pw,
                at=at,
                dot=dot,
                cloudant_api_url=cloudant_api_url,
            ),
            flags=re.IGNORECASE,
        ),
        re.compile(
            r'{http}{cl_account}{colon}{cl_api_key}{at}{cl_account}{dot}{cloudant_api_url}'.format(
                http=http,
                colon=colon,
                cl_account=cl_account,
                cl_api_key=cl_api_key,
                at=at,
                dot=dot,
                cloudant_api_url=cloudant_api_url,
            ),
            flags=re.IGNORECASE,
        ),
    ]

    def verify(self, token, content, potential_secret=None):

        hosts = find_account(content)
        if not hosts:
            return VerifiedResult.UNVERIFIED

        for host in hosts:
            return verify_cloudant_key(host, token, potential_secret)

        return VerifiedResult.VERIFIED_FALSE


def find_account(content):
    opt_hostname_keyword = r'(?:hostname|host|username|id|user|userid|user-id|user-name|' \
        'name|user_id|user_name|uname|account)'
    account = r'(\w[\w\-]*)'
    opt_basic_auth = r'(?:[\w\-:%]*\@)?'

    regexes = (
        RegexBasedDetector.assign_regex_generator(
            prefix_regex=CloudantDetector.cl,
            password_keyword_regex=opt_hostname_keyword,
            password_regex=account,
        ),
        re.compile(
            r'{http}{opt_basic_auth}{cl_account}{dot}{cloudant_api_url}'.format(
                http=CloudantDetector.http,
                opt_basic_auth=opt_basic_auth,
                cl_account=account,
                dot=CloudantDetector.dot,
                cloudant_api_url=CloudantDetector.cloudant_api_url,
            ),
            flags=re.IGNORECASE,
        ),
    )

    return [
        match
        for line in content.splitlines()
        for regex in regexes
        for match in regex.findall(line)
    ]


def verify_cloudant_key(hostname, token, potential_secret=None):
    try:
        headers = {'Content-type': 'application/json'}
        request_url = 'https://{hostname}:' \
            '{token}' \
            '@{hostname}.' \
            'cloudant.com'.format(
                hostname=hostname,
                token=token,
            )

        response = requests.get(
            request_url,
            headers=headers,
        )

        if response.status_code == 200:
            if potential_secret:
                potential_secret.other_factors['hostname'] = hostname
            return VerifiedResult.VERIFIED_TRUE
        else:
            return VerifiedResult.VERIFIED_FALSE
    except requests.exceptions.RequestException:
        return VerifiedResult.UNVERIFIED
