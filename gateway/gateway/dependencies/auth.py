""" AuthenticationHandler """

from os import environ
from flask import request, g
from flask.wrappers import Request, Response
#from flask_oidc import OpenIDConnect
from flask_nameko import FlaskPooledClusterRpcProxy
from requests import post, exceptions
from jwt import decode
from typing import Callable, Union
from keycloak import KeycloakOpenID

from .response import ResponseParser, APIException


class AuthenticationHandler:
    """The AuthenticationHandler connects to the user service and verifies if the bearer token
    send by the user is valid.
    """

    def __init__(self, response_handler: ResponseParser):
        self._res = response_handler

        # Instantiate keycloak client
        self.keycloak_openid = start_keycloak()

    def oidc_token(self, func):
        def decorator(*args, **kwargs):
            try:
                token = self._parse_auth_header(request)

                # Check validity of token
                userinfo = self.keycloak_openid.userinfo(token)
                if userinfo['email_verified']:
                    user_id = userinfo['sub']
                    decorated_function = func(user_id=user_id)
                    return decorated_function
                else:
                    raise APIException(
                        msg="The email address of user {0} is not verified."\
                            .format(user_id),
                        code=401,
                        service="gateway",
                        internal=False)
            except exceptions.HTTPError as exc:
                raise APIException(
                    msg=str(exc),
                    code=401,
                    service="gateway",
                    internal=False)
            except Exception as exc:
                return self._res.error(exc)
        return decorator

    # def oidc(self, f):
    #     def decorator(*args, **kwargs):
    #         try:
    #             if g.oidc_id_token is None:
    #                 return self._oidc.redirect_to_auth_server(request.url)
    #
    #             user_id = self._oidc.user_getfield("sub")
    #
    #             if not self._oidc.user_getfield("email_verified"):
    #                 raise APIException(
    #                     msg="The email address of user {0} is not verified."\
    #                         .format(user_id),
    #                     code=401,
    #                     service="gateway",
    #                     internal=False)
    #
    #             return f(user_id=user_id)
    #         except exceptions.HTTPError as exc:
    #             raise APIException(
    #                 msg=str(exc),
    #                 code=401,
    #                 service="gateway",
    #                 internal=False)
    #         except Exception as exc:
    #             return self._res.error(exc)
    #     return decorator

    def check_role(self, f, role):
        def decorator(user_id=None):
            try:
                token = self._parse_auth_header(request)
                roles = self._get_roles(token)

                if role not in roles:
                    raise APIException(
                        msg="The user {0} is not authorized to access this resources."\
                            .format(user_id),
                        code=403,
                        service="gateway",
                        internal=False)

                return f(user_id=user_id)
            except Exception as exc:
                return self._res.error(exc)
        return decorator

    def _get_roles(self, token):
        roles = []
        if token:
            token_decode = decode(token, algorithms=['HS256'], verify=False)
            roles = token_decode["resource_access"]["openeo"]["roles"]
        return roles

    def _parse_auth_header(self, req: Request) -> Union[str, Exception]:
        """Parses and returns the bearer token. Raises an AuthenticationException if the Authorization
        header in the request is not correct.

        Arguments:
            req {Request} -- The Request object

        Returns:
            Union[str, Exception] -- Returns the bearer token as string or raises an exception
        """

        if "Authorization" not in req.headers or not req.headers["Authorization"]:
            raise APIException(
                msg="Missing 'Authorization' header.",
                code=400,
                service="gateway",
                internal=False)

        token_split = req.headers["Authorization"].split(" ")

        if len(token_split) != 2 or token_split[0] != "Bearer":
            raise APIException(
                msg="Invalid Bearer token.",
                code=401,
                service="gateway",
                internal=False)

        return token_split[1]


    def user_info(self) -> dict:
        """
        Get info about loggedin user from token embedded in the request's headers.
        """

        token = self._parse_auth_header(request)
        userinfo = self.keycloak_openid.userinfo(token)

        user_info = {}
        user_info['userid'] = userinfo['sub']
        user_info['email'] = userinfo['email']

        return user_info

def start_keycloak():
    """
    Start Keycloak client according to credentials stored in env variables.
    """

    # Instantiate keycloak client
    keycloak_openid = KeycloakOpenID(
        server_url=environ.get('OIDC_URL'),
        realm_name=environ.get('OIDC_REALM'),
        client_id=environ.get('OIDC_CLIENT_ID'),
        client_secret_key=environ.get('OIDC_CLIENT_SECRET'))

    return keycloak_openid
