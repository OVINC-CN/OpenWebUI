from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from typing import Optional, Literal

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.config import get_config, save_config
from open_webui.config import BannerModel

from open_webui.utils.tools import get_tool_server_data, get_tool_servers_data

router = APIRouter()


############################
# ImportConfig
############################


class ImportConfigForm(BaseModel):
    config: dict


@router.post("/import", response_model=dict)
async def import_config(form_data: ImportConfigForm, user=Depends(get_admin_user)):
    save_config(form_data.config)
    return get_config()


############################
# ExportConfig
############################


@router.get("/export", response_model=dict)
async def export_config(user=Depends(get_admin_user)):
    return get_config()


############################
# Direct Connections Config
############################


class DirectConnectionsConfigForm(BaseModel):
    ENABLE_DIRECT_CONNECTIONS: bool


@router.get("/direct_connections", response_model=DirectConnectionsConfigForm)
async def get_direct_connections_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_DIRECT_CONNECTIONS": request.app.state.config.ENABLE_DIRECT_CONNECTIONS,
    }


@router.post("/direct_connections", response_model=DirectConnectionsConfigForm)
async def set_direct_connections_config(
    request: Request,
    form_data: DirectConnectionsConfigForm,
    user=Depends(get_admin_user),
):
    request.app.state.config.ENABLE_DIRECT_CONNECTIONS = (
        form_data.ENABLE_DIRECT_CONNECTIONS
    )
    return {
        "ENABLE_DIRECT_CONNECTIONS": request.app.state.config.ENABLE_DIRECT_CONNECTIONS,
    }


############################
# ToolServers Config
############################


class ToolServerConnection(BaseModel):
    url: str
    path: str
    auth_type: Optional[str]
    key: Optional[str]
    config: Optional[dict]

    model_config = ConfigDict(extra="allow")


class ToolServersConfigForm(BaseModel):
    TOOL_SERVER_CONNECTIONS: list[ToolServerConnection]


@router.get("/tool_servers", response_model=ToolServersConfigForm)
async def get_tool_servers_config(request: Request, user=Depends(get_admin_user)):
    return {
        "TOOL_SERVER_CONNECTIONS": request.app.state.config.TOOL_SERVER_CONNECTIONS,
    }


@router.post("/tool_servers", response_model=ToolServersConfigForm)
async def set_tool_servers_config(
    request: Request,
    form_data: ToolServersConfigForm,
    user=Depends(get_admin_user),
):
    request.app.state.config.TOOL_SERVER_CONNECTIONS = [
        connection.model_dump() for connection in form_data.TOOL_SERVER_CONNECTIONS
    ]

    request.app.state.TOOL_SERVERS = await get_tool_servers_data(
        request.app.state.config.TOOL_SERVER_CONNECTIONS
    )

    return {
        "TOOL_SERVER_CONNECTIONS": request.app.state.config.TOOL_SERVER_CONNECTIONS,
    }


@router.post("/tool_servers/verify")
async def verify_tool_servers_config(
    request: Request, form_data: ToolServerConnection, user=Depends(get_admin_user)
):
    """
    Verify the connection to the tool server.
    """
    try:

        token = None
        if form_data.auth_type == "bearer":
            token = form_data.key
        elif form_data.auth_type == "session":
            token = request.state.token.credentials

        url = f"{form_data.url}/{form_data.path}"
        return await get_tool_server_data(token, url)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to the tool server: {str(e)}",
        )


############################
# CodeInterpreterConfig
############################
class CodeInterpreterConfigForm(BaseModel):
    ENABLE_CODE_EXECUTION: bool
    CODE_EXECUTION_ENGINE: str
    CODE_EXECUTION_JUPYTER_URL: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH_TOKEN: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH_PASSWORD: Optional[str]
    CODE_EXECUTION_JUPYTER_TIMEOUT: Optional[int]
    ENABLE_CODE_INTERPRETER: bool
    CODE_INTERPRETER_ENGINE: str
    CODE_INTERPRETER_PROMPT_TEMPLATE: Optional[str]
    CODE_INTERPRETER_JUPYTER_URL: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH_TOKEN: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD: Optional[str]
    CODE_INTERPRETER_JUPYTER_TIMEOUT: Optional[int]


@router.get("/code_execution", response_model=CodeInterpreterConfigForm)
async def get_code_execution_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_CODE_EXECUTION": request.app.state.config.ENABLE_CODE_EXECUTION,
        "CODE_EXECUTION_ENGINE": request.app.state.config.CODE_EXECUTION_ENGINE,
        "CODE_EXECUTION_JUPYTER_URL": request.app.state.config.CODE_EXECUTION_JUPYTER_URL,
        "CODE_EXECUTION_JUPYTER_AUTH": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH,
        "CODE_EXECUTION_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN,
        "CODE_EXECUTION_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD,
        "CODE_EXECUTION_JUPYTER_TIMEOUT": request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT,
        "ENABLE_CODE_INTERPRETER": request.app.state.config.ENABLE_CODE_INTERPRETER,
        "CODE_INTERPRETER_ENGINE": request.app.state.config.CODE_INTERPRETER_ENGINE,
        "CODE_INTERPRETER_PROMPT_TEMPLATE": request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE,
        "CODE_INTERPRETER_JUPYTER_URL": request.app.state.config.CODE_INTERPRETER_JUPYTER_URL,
        "CODE_INTERPRETER_JUPYTER_AUTH": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH,
        "CODE_INTERPRETER_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN,
        "CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD,
        "CODE_INTERPRETER_JUPYTER_TIMEOUT": request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT,
    }


@router.post("/code_execution", response_model=CodeInterpreterConfigForm)
async def set_code_execution_config(
    request: Request, form_data: CodeInterpreterConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_CODE_EXECUTION = form_data.ENABLE_CODE_EXECUTION

    request.app.state.config.CODE_EXECUTION_ENGINE = form_data.CODE_EXECUTION_ENGINE
    request.app.state.config.CODE_EXECUTION_JUPYTER_URL = (
        form_data.CODE_EXECUTION_JUPYTER_URL
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH = (
        form_data.CODE_EXECUTION_JUPYTER_AUTH
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN = (
        form_data.CODE_EXECUTION_JUPYTER_AUTH_TOKEN
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD = (
        form_data.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT = (
        form_data.CODE_EXECUTION_JUPYTER_TIMEOUT
    )

    request.app.state.config.ENABLE_CODE_INTERPRETER = form_data.ENABLE_CODE_INTERPRETER
    request.app.state.config.CODE_INTERPRETER_ENGINE = form_data.CODE_INTERPRETER_ENGINE
    request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE = (
        form_data.CODE_INTERPRETER_PROMPT_TEMPLATE
    )

    request.app.state.config.CODE_INTERPRETER_JUPYTER_URL = (
        form_data.CODE_INTERPRETER_JUPYTER_URL
    )

    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH = (
        form_data.CODE_INTERPRETER_JUPYTER_AUTH
    )

    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN = (
        form_data.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN
    )
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD = (
        form_data.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD
    )
    request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT = (
        form_data.CODE_INTERPRETER_JUPYTER_TIMEOUT
    )

    return {
        "ENABLE_CODE_EXECUTION": request.app.state.config.ENABLE_CODE_EXECUTION,
        "CODE_EXECUTION_ENGINE": request.app.state.config.CODE_EXECUTION_ENGINE,
        "CODE_EXECUTION_JUPYTER_URL": request.app.state.config.CODE_EXECUTION_JUPYTER_URL,
        "CODE_EXECUTION_JUPYTER_AUTH": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH,
        "CODE_EXECUTION_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN,
        "CODE_EXECUTION_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD,
        "CODE_EXECUTION_JUPYTER_TIMEOUT": request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT,
        "ENABLE_CODE_INTERPRETER": request.app.state.config.ENABLE_CODE_INTERPRETER,
        "CODE_INTERPRETER_ENGINE": request.app.state.config.CODE_INTERPRETER_ENGINE,
        "CODE_INTERPRETER_PROMPT_TEMPLATE": request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE,
        "CODE_INTERPRETER_JUPYTER_URL": request.app.state.config.CODE_INTERPRETER_JUPYTER_URL,
        "CODE_INTERPRETER_JUPYTER_AUTH": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH,
        "CODE_INTERPRETER_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN,
        "CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD,
        "CODE_INTERPRETER_JUPYTER_TIMEOUT": request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT,
    }


############################
# SetDefaultModels
############################
class ModelsConfigForm(BaseModel):
    DEFAULT_MODELS: Optional[str]
    MODEL_ORDER_LIST: Optional[list[str]]


@router.get("/models", response_model=ModelsConfigForm)
async def get_models_config(request: Request, user=Depends(get_admin_user)):
    return {
        "DEFAULT_MODELS": request.app.state.config.DEFAULT_MODELS,
        "MODEL_ORDER_LIST": request.app.state.config.MODEL_ORDER_LIST,
    }


@router.post("/models", response_model=ModelsConfigForm)
async def set_models_config(
    request: Request, form_data: ModelsConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.DEFAULT_MODELS = form_data.DEFAULT_MODELS
    request.app.state.config.MODEL_ORDER_LIST = form_data.MODEL_ORDER_LIST
    return {
        "DEFAULT_MODELS": request.app.state.config.DEFAULT_MODELS,
        "MODEL_ORDER_LIST": request.app.state.config.MODEL_ORDER_LIST,
    }


class PromptSuggestion(BaseModel):
    title: list[str]
    content: str


class SetDefaultSuggestionsForm(BaseModel):
    suggestions: list[PromptSuggestion]


@router.post("/suggestions", response_model=list[PromptSuggestion])
async def set_default_suggestions(
    request: Request,
    form_data: SetDefaultSuggestionsForm,
    user=Depends(get_admin_user),
):
    data = form_data.model_dump()
    request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS = data["suggestions"]
    return request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS


############################
# SetBanners
############################


class SetBannersForm(BaseModel):
    banners: list[BannerModel]


@router.post("/banners", response_model=list[BannerModel])
async def set_banners(
    request: Request,
    form_data: SetBannersForm,
    user=Depends(get_admin_user),
):
    data = form_data.model_dump()
    request.app.state.config.BANNERS = data["banners"]
    return request.app.state.config.BANNERS


@router.get("/banners", response_model=list[BannerModel])
async def get_banners(
    request: Request,
    user=Depends(get_verified_user),
):
    return request.app.state.config.BANNERS


############################
# Usage
############################


class UsageConfigForm(BaseModel):
    CREDIT_NO_CREDIT_MSG: str = Field(default="余额不足，请前往 设置-积分 充值")
    CREDIT_EXCHANGE_RATIO: float = Field(default=1, gt=0)
    CREDIT_DEFAULT_CREDIT: float = Field(default=0, ge=0)
    USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE: str = Field(default="")
    USAGE_DEFAULT_ENCODING_MODEL: str = Field(default="gpt-4o")
    USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE: float = Field(default=0, ge=0)
    USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE: float = Field(default=0, ge=0)
    USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE: float = Field(default=0, ge=0)
    USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE: float = Field(default=0, ge=0)
    USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE: float = Field(default=0, ge=0)
    USAGE_CALCULATE_MINIMUM_COST: float = Field(default=0, ge=0)
    EZFP_PAY_PRIORITY: Literal["qrcode", "link"] = Field(default="qrcode")
    EZFP_ENDPOINT: Optional[str] = None
    EZFP_PID: Optional[str] = None
    EZFP_KEY: Optional[str] = None
    EZFP_CALLBACK_HOST: Optional[str] = None
    EZFP_AMOUNT_CONTROL: Optional[str] = None


@router.get("/usage", response_model=UsageConfigForm)
async def get_usage_config(request: Request, user=Depends(get_admin_user)):
    return {
        "CREDIT_NO_CREDIT_MSG": request.app.state.config.CREDIT_NO_CREDIT_MSG,
        "CREDIT_EXCHANGE_RATIO": request.app.state.config.CREDIT_EXCHANGE_RATIO,
        "CREDIT_DEFAULT_CREDIT": request.app.state.config.CREDIT_DEFAULT_CREDIT,
        "USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE": request.app.state.config.USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE,
        "USAGE_DEFAULT_ENCODING_MODEL": request.app.state.config.USAGE_DEFAULT_ENCODING_MODEL,
        "USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE": request.app.state.config.USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE,
        "USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE,
        "USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE,
        "USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE,
        "USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE,
        "USAGE_CALCULATE_MINIMUM_COST": request.app.state.config.USAGE_CALCULATE_MINIMUM_COST,
        "EZFP_PAY_PRIORITY": request.app.state.config.EZFP_PAY_PRIORITY,
        "EZFP_ENDPOINT": request.app.state.config.EZFP_ENDPOINT,
        "EZFP_PID": request.app.state.config.EZFP_PID,
        "EZFP_KEY": request.app.state.config.EZFP_KEY,
        "EZFP_CALLBACK_HOST": request.app.state.config.EZFP_CALLBACK_HOST,
        "EZFP_AMOUNT_CONTROL": request.app.state.config.EZFP_AMOUNT_CONTROL,
    }


@router.post("/usage", response_model=UsageConfigForm)
async def set_usage_config(
    request: Request, form_data: UsageConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.CREDIT_NO_CREDIT_MSG = form_data.CREDIT_NO_CREDIT_MSG
    request.app.state.config.CREDIT_EXCHANGE_RATIO = form_data.CREDIT_EXCHANGE_RATIO
    request.app.state.config.CREDIT_DEFAULT_CREDIT = form_data.CREDIT_DEFAULT_CREDIT
    request.app.state.config.USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE = (
        form_data.USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE
    )
    request.app.state.config.USAGE_DEFAULT_ENCODING_MODEL = (
        form_data.USAGE_DEFAULT_ENCODING_MODEL
    )
    request.app.state.config.USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE = (
        form_data.USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE
    )
    request.app.state.config.USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE = (
        form_data.USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE
    )
    request.app.state.config.USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE = (
        form_data.USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE
    )
    request.app.state.config.USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE = (
        form_data.USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE
    )
    request.app.state.config.USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE = (
        form_data.USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE
    )
    request.app.state.config.USAGE_CALCULATE_MINIMUM_COST = (
        form_data.USAGE_CALCULATE_MINIMUM_COST
    )
    request.app.state.config.EZFP_PAY_PRIORITY = form_data.EZFP_PAY_PRIORITY
    request.app.state.config.EZFP_ENDPOINT = form_data.EZFP_ENDPOINT
    request.app.state.config.EZFP_PID = form_data.EZFP_PID
    request.app.state.config.EZFP_KEY = form_data.EZFP_KEY
    request.app.state.config.EZFP_CALLBACK_HOST = form_data.EZFP_CALLBACK_HOST
    request.app.state.config.EZFP_AMOUNT_CONTROL = form_data.EZFP_AMOUNT_CONTROL

    return {
        "CREDIT_NO_CREDIT_MSG": request.app.state.config.CREDIT_NO_CREDIT_MSG,
        "USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE": request.app.state.config.USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE,
        "USAGE_DEFAULT_ENCODING_MODEL": request.app.state.config.USAGE_DEFAULT_ENCODING_MODEL,
        "USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE": request.app.state.config.USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE,
        "USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE,
        "USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE,
        "USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE,
        "USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE": request.app.state.config.USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE,
        "USAGE_CALCULATE_MINIMUM_COST": request.app.state.config.USAGE_CALCULATE_MINIMUM_COST,
        "EZFP_PAY_PRIORITY": request.app.state.config.EZFP_PAY_PRIORITY,
        "EZFP_ENDPOINT": request.app.state.config.EZFP_ENDPOINT,
        "EZFP_PID": request.app.state.config.EZFP_PID,
        "EZFP_KEY": request.app.state.config.EZFP_KEY,
        "EZFP_CALLBACK_HOST": request.app.state.config.EZFP_CALLBACK_HOST,
        "EZFP_AMOUNT_CONTROL": request.app.state.config.EZFP_AMOUNT_CONTROL,
    }
