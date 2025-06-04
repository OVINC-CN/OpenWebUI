import logging
import shutil
import uuid
import jwt
import base64
import hmac
import hashlib
import requests
import os

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
    WEBUI_SECRET_KEY,
    TRUSTED_SIGNATURE_KEY,
    STATIC_DIR,
    SRC_LOG_LEVELS,
    FRONTEND_BUILD_DIR,
    REDIS_URL,
    REDIS_SENTINEL_HOSTS,
    REDIS_SENTINEL_PORT,
    WEBUI_NAME,
)

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from open_webui.utils.redis import get_redis_connection, get_sentinels_from_env

logging.getLogger("passlib").setLevel(logging.ERROR)

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
            "organization_name": os.getenv("ORGANIZATION_NAME", "OpenWebui"),
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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return (
        pwd_context.verify(plain_password, hashed_password) if hashed_password else None
    )


def get_password_hash(password):
    return pwd_context.hash(password)


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
    background_tasks: BackgroundTasks,
    auth_token: HTTPAuthorizationCredentials = Depends(bearer_security),
):
    token = None

    if auth_token is not None:
        token = auth_token.credentials

    if token is None and "token" in request.cookies:
        token = request.cookies.get("token")

    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

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
                background_tasks.add_task(Users.update_user_last_active_by_id, user.id)
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


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


verify_email_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%(title)s</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 0; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(90deg, #667eea 0%%, #764ba2 100%%); color: #ffffff; text-align: center; padding: 30px 20px; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 300; }
        .content { padding: 40px 30px; }
        .content h2 { color: #333333; margin-top: 0; font-size: 24px; font-weight: 600; }
        .content p { color: #666666; line-height: 1.6; margin: 15px 0; font-size: 16px; }
        .button { display: inline-block; background: linear-gradient(90deg, #667eea 0%%, #764ba2 100%%); color: #667eea; text-decoration: none; padding: 15px 30px; border-radius: 50px; font-weight: 600; margin: 20px 0; text-align: center; font-size: 16px; }
        .button:hover { opacity: 0.9; }
        .footer { background-color: #f8f9fa; color: #6c757d; text-align: center; padding: 20px; font-size: 14px; }
        .logo { width: 50px; height: 50px; margin: 0 auto 20px; background: #ffffff; border-radius: 50%%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Comi</div>
            <h1>%(title)s</h1>
        </div>
        <div class="content">
            <h2>点击下方链接验证您的邮箱</h2>
            <p>您好！感谢您注册我们的服务。请点击下方按钮来验证您的邮箱地址。</p>
            <p style="text-align: center;">
                <a href="%(link)s" class="button">验证邮箱</a>
            </p>
            <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
            <p style="word-break: break-all; background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace;">%(link)s</p>
            <p><strong>注意：</strong>此链接将在24小时后失效。</p>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿回复。</p>
        </div>
    </div>
</body>
</html>
"""


password_reset_email_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%(title)s</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 0; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(90deg, #667eea 0%%, #764ba2 100%%); color: #ffffff; text-align: center; padding: 30px 20px; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 300; }
        .content { padding: 40px 30px; }
        .content h2 { color: #333333; margin-top: 0; font-size: 24px; font-weight: 600; }
        .content p { color: #666666; line-height: 1.6; margin: 15px 0; font-size: 16px; }
        .button { display: inline-block; background: linear-gradient(90deg, #667eea 0%%, #764ba2 100%%); color: #667eea; text-decoration: none; padding: 15px 30px; border-radius: 50px; font-weight: 600; margin: 20px 0; text-align: center; font-size: 16px; }
        .button:hover { opacity: 0.9; }
        .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { background-color: #f8f9fa; color: #6c757d; text-align: center; padding: 20px; font-size: 14px; }
        .logo { width: 50px; height: 50px; margin: 0 auto 20px; background: #ffffff; border-radius: 50%%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Comi</div>
            <h1>%(title)s</h1>
        </div>
        <div class="content">
            <h2>重置您的密码</h2>
            <p>您好！我们收到了重置您账户密码的请求。</p>
            <p>请点击下方按钮来重置您的密码：</p>
            <p style="text-align: center;">
                <a href="%(link)s" class="button">重置密码</a>
            </p>
            <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
            <p style="word-break: break-all; background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace;">%(link)s</p>
            <div class="warning">
                <strong>重要提醒：</strong>
                <ul style="margin: 10px 0 0 20px;">
                    <li>此链接将在1小时后失效</li>
                    <li>如果您没有请求重置密码，请忽略此邮件</li>
                    <li>为了您的账户安全，建议设置强密码</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿回复。</p>
        </div>
    </div>
</body>
</html>
"""


def get_email_code_key(code: str) -> str:
    return f"email_verify:{code}"


def get_password_reset_key(code: str) -> str:
    return f"password_reset:{code}"


def send_verify_email(email: str):
    redis = get_redis_connection(
        redis_url=REDIS_URL,
        redis_sentinels=get_sentinels_from_env(
            REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
        ),
    )
    code = f"{uuid.uuid4().hex}{uuid.uuid1().hex}"
    redis.set(name=get_email_code_key(code=code), value=email, ex=timedelta(days=1))
    link = f"{WEBUI_URL.value.rstrip('/')}/api/v1/auths/signup_verify/{code}"
    send_email(
        receiver=email,
        subject=f"Comi AI 邮箱验证",
        body=verify_email_template
        % {"title": f"Comi AI 邮箱验证", "link": link},
    )


def send_password_reset_email(email: str):
    redis = get_redis_connection(
        redis_url=REDIS_URL,
        redis_sentinels=get_sentinels_from_env(
            REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
        ),
    )
    code = f"{uuid.uuid4().hex}{uuid.uuid1().hex}"
    redis.set(name=get_password_reset_key(code=code), value=email, ex=timedelta(hours=1))
    link = f"{WEBUI_URL.value.rstrip('/')}/auth/reset-password?token={code}"
    send_email(
        receiver=email,
        subject=f"重置您的密码 - {WEBUI_NAME}",
        body=password_reset_email_template
        % {"title": f"重置您的密码 - {WEBUI_NAME}", "link": link},
    )


def verify_password_reset_token(token: str) -> str:
    redis = get_redis_connection(
        redis_url=REDIS_URL,
        redis_sentinels=get_sentinels_from_env(
            REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
        ),
    )
    email = redis.get(name=get_password_reset_key(code=token))
    if email:
        # 用完即删除token
        redis.delete(get_password_reset_key(code=token))
    return email


def verify_email_by_code(code: str) -> str:
    redis = get_redis_connection(
        redis_url=REDIS_URL,
        redis_sentinels=get_sentinels_from_env(
            REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
        ),
    )
    return redis.get(name=get_email_code_key(code=code))


async def verify_recaptcha(token: str, secret_key: str) -> bool:
    """
    验证reCAPTCHA令牌
    """
    if not token or not secret_key:
        return False
        
    try:
        data = {
            'secret': secret_key,
            'response': token
        }
        
        response = requests.post(
            'https://www.recaptcha.net/recaptcha/api/siteverify',
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False)
        
    except Exception as e:
        log.error(f"reCAPTCHA验证失败: {str(e)}")
        
    return False
