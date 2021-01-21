import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen

AUTH0_DOMAIN = 'cjohannb.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee_shop'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
def get_token_auth_header():
    """Gets access bearer token from authorization header"""
    #Get authorization form request header
    auth = request.headers.get('Authorization', None)
    #Check if authorization header exists
    if not auth:
        raise AuthError({
        'code': 'authorization_header_missing',
        'description': 'Authorization header is MISSING!'
        }, 401)
    #If bearer token, then first part of string = 'bearer'
    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header (JWT token) must start with "Bearer"'
        }, 401)
    #Authorization header string length must be 2
    elif len(parts) != 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be a BEARER token'
        }, 401)

    token = parts[1]
    return token


# API permission must be in JWT
def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permission NOT included in JWT!'
        }, 400)
    #If permission is empty, then no user is not authorized
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Forbidden access (permission NOT found)'
        }, 403)

'''
    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    # Get Json Web Key Set -> Public key of asymmetric signature
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    # Get data in token header of current session/user -> Private key
    unverified_header = jwt.get_unverified_header(token)
    # Check if token has kid key
    if "kid" not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization NOT correctly formatted!'
        }, 401)

    # Get RSA Key
    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    # Validate key
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired!'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer!'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token!'
            }, 400)
    raise AuthError({
            'code': 'invalid_header',
            'description': 'Unable to find the appropriate key!'
        }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
                print('### Payload:', payload)
            except:
                abort(401)

            check_permissions(permission, payload)

            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
