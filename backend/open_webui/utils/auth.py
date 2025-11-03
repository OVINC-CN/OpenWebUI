import logging
import shutil
import uuid
import jwt
import base64
import hmac
import hashlib
import requests
import os
import bcrypt

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import json


from datetime import datetime, timedelta
import pytz
from pytz import UTC
from typing import Optional, Union, List, Dict

from opentelemetry import trace

from open_webui.config import WEBUI_URL
from open_webui.utils.smtp import send_email

from open_webui.models.users import Users

from open_webui.constants import ERROR_MESSAGES

from open_webui.env import (
    OFFLINE_MODE,
    LICENSE_BLOB,
    pk,
    WEBUI_SECRET_KEY,
    TRUSTED_SIGNATURE_KEY,
    STATIC_DIR,
    SRC_LOG_LEVELS,
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER,
    FRONTEND_BUILD_DIR,
    REDIS_URL,
    REDIS_SENTINEL_HOSTS,
    REDIS_SENTINEL_PORT,
    WEBUI_NAME,
    REDIS_CLUSTER,
)

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from open_webui.utils.redis import get_redis_connection, get_sentinels_from_env

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

SESSION_SECRET = WEBUI_SECRET_KEY
ALGORITHM = "HS256"


##############
# Auth Utils
##############


def verify_signature(payload: str, signature: str) -> bool:
    """
    Verifies the HMAC signature of the received payload.
    """
    try:
        expected_signature = base64.b64encode(
            hmac.new(TRUSTED_SIGNATURE_KEY, payload.encode(), hashlib.sha256).digest()
        ).decode()

        # Compare securely to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)

    except Exception:
        return False


def override_static(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    r = requests.get(content, stream=True)
    with open(path, "wb") as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)


def get_license_data(app, key):
    payload = {
        "resources": {
            os.path.join(STATIC_DIR, "logo.png"): os.getenv("CUSTOM_PNG", ""),
            os.path.join(STATIC_DIR, "favicon.png"): os.getenv("CUSTOM_PNG", ""),
            os.path.join(STATIC_DIR, "favicon.svg"): os.getenv("CUSTOM_SVG", ""),
            os.path.join(STATIC_DIR, "favicon-96x96.png"): os.getenv("CUSTOM_PNG", ""),
            os.path.join(STATIC_DIR, "apple-touch-icon.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(STATIC_DIR, "web-app-manifest-192x192.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(STATIC_DIR, "web-app-manifest-512x512.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(STATIC_DIR, "splash.png"): os.getenv("CUSTOM_PNG", ""),
            os.path.join(STATIC_DIR, "favicon.ico"): os.getenv("CUSTOM_ICO", ""),
            os.path.join(STATIC_DIR, "favicon-dark.png"): os.getenv(
                "CUSTOM_DARK_PNG", ""
            ),
            os.path.join(STATIC_DIR, "splash-dark.png"): os.getenv(
                "CUSTOM_DARK_PNG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "favicon.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/favicon.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/favicon.svg"): os.getenv(
                "CUSTOM_SVG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/favicon-96x96.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/apple-touch-icon.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(
                FRONTEND_BUILD_DIR, "static/web-app-manifest-192x192.png"
            ): os.getenv("CUSTOM_PNG", ""),
            os.path.join(
                FRONTEND_BUILD_DIR, "static/web-app-manifest-512x512.png"
            ): os.getenv("CUSTOM_PNG", ""),
            os.path.join(FRONTEND_BUILD_DIR, "static/splash.png"): os.getenv(
                "CUSTOM_PNG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/favicon.ico"): os.getenv(
                "CUSTOM_ICO", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/favicon-dark.png"): os.getenv(
                "CUSTOM_DARK_PNG", ""
            ),
            os.path.join(FRONTEND_BUILD_DIR, "static/splash-dark.png"): os.getenv(
                "CUSTOM_DARK_PNG", ""
            ),
        },
        "metadata": {
            "type": "enterprise",
            "organization_name": os.getenv("ORGANIZATION_NAME", "cheny"),
        },
    }
    try:
        for k, v in payload.items():
            if k == "resources":
                for p, c in v.items():
                    if c:
                        globals().get("override_static", lambda a, b: None)(p, c)
            elif k == "count":
                setattr(app.state, "USER_COUNT", v)
            elif k == "name":
                setattr(app.state, "WEBUI_NAME", v)
            elif k == "metadata":
                setattr(app.state, "LICENSE_METADATA", v)
        return True
    except Exception as ex:
        log.exception(f"License: Uncaught Exception: {ex}")

    return True


bearer_security = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return (
        bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
        if hashed_password
        else None
    )


def create_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    payload = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        payload.update({"exp": expire})

    encoded_jwt = jwt.encode(payload, SESSION_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        decoded = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
        return decoded
    except Exception:
        return None


def extract_token_from_auth_header(auth_header: str):
    return auth_header[len("Bearer ") :]


def create_api_key():
    key = str(uuid.uuid4()).replace("-", "")
    return f"sk-{key}"


def get_http_authorization_cred(auth_header: Optional[str]):
    if not auth_header:
        return None
    try:
        scheme, credentials = auth_header.split(" ")
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
    except Exception:
        return None


def get_current_user(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    auth_token: HTTPAuthorizationCredentials = Depends(bearer_security),
):
    token = None

    if auth_token is not None:
        token = auth_token.credentials

    if token is None and "token" in request.cookies:
        token = request.cookies.get("token")

    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # auth by api key
    if token.startswith("sk-"):
        if not request.state.enable_api_key:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.API_KEY_NOT_ALLOWED
            )

        if request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS:
            allowed_paths = [
                path.strip()
                for path in str(
                    request.app.state.config.API_KEY_ALLOWED_ENDPOINTS
                ).split(",")
            ]

            # Check if the request path matches any allowed endpoint.
            if not any(
                request.url.path == allowed
                or request.url.path.startswith(allowed + "/")
                for allowed in allowed_paths
            ):
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.API_KEY_NOT_ALLOWED
                )

        user = get_current_user_by_api_key(token)

        # Add user info to current span
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute("client.user.id", user.id)
            current_span.set_attribute("client.user.email", user.email)
            current_span.set_attribute("client.user.role", user.role)
            current_span.set_attribute("client.auth.type", "api_key")

        return user

    # auth by jwt token

    try:
        try:
            data = decode_token(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        if data is not None and "id" in data:
            user = Users.get_user_by_id(data["id"])
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=ERROR_MESSAGES.INVALID_TOKEN,
                )
            else:
                if WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
                    trusted_email = request.headers.get(
                        WEBUI_AUTH_TRUSTED_EMAIL_HEADER, ""
                    ).lower()
                    if trusted_email and user.email != trusted_email:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User mismatch. Please sign in again.",
                        )

                # Add user info to current span
                current_span = trace.get_current_span()
                if current_span:
                    current_span.set_attribute("client.user.id", user.id)
                    current_span.set_attribute("client.user.email", user.email)
                    current_span.set_attribute("client.user.role", user.role)
                    current_span.set_attribute("client.auth.type", "jwt")

                # Refresh the user's last active timestamp asynchronously
                # to prevent blocking the request
                if background_tasks:
                    background_tasks.add_task(
                        Users.update_user_last_active_by_id, user.id
                    )
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.UNAUTHORIZED,
            )
    except Exception as e:
        # Delete the token cookie
        if request.cookies.get("token"):
            response.delete_cookie("token")

        if request.cookies.get("oauth_id_token"):
            response.delete_cookie("oauth_id_token")

        # Delete OAuth session if present
        if request.cookies.get("oauth_session_id"):
            response.delete_cookie("oauth_session_id")

        raise e


def get_current_user_by_api_key(api_key: str):
    user = Users.get_user_by_api_key(api_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.INVALID_TOKEN,
        )
    else:
        # Add user info to current span
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute("client.user.id", user.id)
            current_span.set_attribute("client.user.email", user.email)
            current_span.set_attribute("client.user.role", user.role)
            current_span.set_attribute("client.auth.type", "api_key")

        Users.update_user_last_active_by_id(user.id)

    return user


def get_verified_user(user=Depends(get_current_user)):
    if user.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user


def get_admin_user(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user


verify_email_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>账户激活</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', Arial, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }
        
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .email-header {
            background: linear-gradient(135deg, #6B73FF 0%%, #5DADE2 100%%);
            padding: 30px;
            text-align: center;
        }
        
        .email-header img {
            max-width: 100px;
            height: auto;
        }
        
        .email-header h1 {
            color: white;
            font-size: 24px;
            margin-top: 15px;
            font-weight: 600;
        }
        
        .email-content {
            padding: 40px 30px;
            text-align: center;
        }
        
        .welcome-text {
            font-size: 18px;
            margin-bottom: 25px;
            color: #2c3e50;
        }
        
        .instruction-text {
            font-size: 16px;
            margin-bottom: 30px;
            color: #5d6778;
        }
        
        .activate-button {
            display: inline-block;
            background: linear-gradient(to right, #5D8CF7, #4286F5);
            color: white;
            text-decoration: none;
            padding: 14px 30px;
            border-radius: 50px;
            font-weight: 500;
            font-size: 16px;
            margin: 20px 0;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(65, 132, 234, 0.35);
        }
        
        .activate-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(65, 132, 234, 0.40);
        }
        
        .note {
            font-size: 14px;
            color: #8a94a6;
            margin-top: 30px;
        }
        
        .email-footer {
            background-color: #f8fafc;
            padding: 20px;
            text-align: center;
            font-size: 13px;
            color: #8a94a6;
            border-top: 1px solid #eaeef3;
        }
        
        .social-links {
            margin: 15px 0;
        }
        
        .social-link {
            display: inline-block;
            margin: 0 8px;
            width: 32px;
            height: 32px;
            background-color: #e1e5eb;
            border-radius: 50%%;
            line-height: 32px;
            text-align: center;
            transition: background-color 0.3s ease;
        }
        
        .social-link:hover {
            background-color: #d0d5dd;
        }
        
        @media only screen and (max-width: 600px) {
            .email-container {
                border-radius: 0;
            }
            
            .email-header, .email-content {
                padding: 25px 20px;
            }
            
            .email-header h1 {
                font-size: 22px;
            }
            
            .welcome-text {
                font-size: 16px;
            }
            
            .instruction-text {
                font-size: 15px;
            }
            
            .activate-button {
                padding: 12px 25px;
                font-size: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>%(title)s</h1>
        </div>
        
        <div class="email-content">
            <p class="instruction-text">请点击下方按钮激活您的账户，开始精彩体验。激活链接有效期为24小时。</p>
            <a href="%(link)s" class="activate-button">立即激活账户</a>
            <p class="note">如果您没有注册我们的服务，请忽略此邮件。</p>
        </div>
    </div>
</body>
</html>"""


def get_email_code_key(code: str) -> str:
    return f"email_verify:{code}"


def send_verify_email(email: str):
    redis = get_redis_connection(
        redis_url=REDIS_URL,
        redis_sentinels=get_sentinels_from_env(
            REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
        ),
        redis_cluster=REDIS_CLUSTER,
    )
    code = f"{uuid.uuid4().hex}{uuid.uuid1().hex}"
    redis.set(name=get_email_code_key(code=code), value=email, ex=timedelta(days=1))
    link = f"{WEBUI_URL.value.rstrip('/')}/api/v1/auths/signup_verify/{code}"
    send_email(
        receiver=email,
        subject=f"{WEBUI_NAME} Email Verify",
        body=verify_email_template
        % {"title": f"{WEBUI_NAME} Email Verify", "link": link},
    )


def verify_email_by_code(code: str) -> str:
    redis = get_redis_connection(
        redis_url=REDIS_URL,
        redis_sentinels=get_sentinels_from_env(
            REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
        ),
        redis_cluster=REDIS_CLUSTER,
    )
    return redis.get(name=get_email_code_key(code=code))
