import datetime
import json
import logging
import time
import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from pydantic import BaseModel, Field

from open_webui.config import EZFP_CALLBACK_HOST, ALIPAY_APP_ID
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.credits import (
    TradeTicketModel,
    TradeTickets,
    CreditLogSimpleModel,
    CreditLogs,
    RedemptionCodes,
    RedemptionCodeModel,
)
from open_webui.models.models import Models, ModelPriceForm
from open_webui.models.users import UserModel, Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.utils.credit.alipay import AlipayClient
from open_webui.utils.credit.ezfp import ezfp_client
from open_webui.utils.models import get_all_models

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()

PAGE_ITEM_COUNT = 30


@router.get("/config")
async def get_config(request: Request):
    return {
        "CREDIT_EXCHANGE_RATIO": request.app.state.config.CREDIT_EXCHANGE_RATIO,
        "EZFP_PAY_PRIORITY": request.app.state.config.EZFP_PAY_PRIORITY,
    }


@router.get("/logs", response_model=list[CreditLogSimpleModel])
async def list_credit_logs(
    page: Optional[int] = None, user: UserModel = Depends(get_verified_user)
) -> TradeTicketModel:
    if page:
        limit = PAGE_ITEM_COUNT
        offset = (page - 1) * limit
        return CreditLogs.get_credit_log_by_page(
            user_ids=[user.id], offset=offset, limit=limit
        )
    else:
        return CreditLogs.get_credit_log_by_page(user_ids=[user.id], offset=0, limit=10)


class DeleteLogsForm(BaseModel):
    timestamp: int = Field(gt=0)


class DeleteLogsResponse(BaseModel):
    affect_rows: int


@router.delete("/logs")
async def update_model_price(
    form_data: DeleteLogsForm, _: UserModel = Depends(get_admin_user)
) -> DeleteLogsResponse:
    return DeleteLogsResponse(
        affect_rows=CreditLogs.delete_log_by_timestamp(form_data.timestamp)
    )


@router.get("/all_logs")
async def get_all_logs(
    query: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    _: UserModel = Depends(get_admin_user),
):
    # init params
    page = page or 1
    limit = limit or PAGE_ITEM_COUNT
    offset = (page - 1) * limit
    # query users
    users = Users.get_users(filter={"query": query})
    user_map = {user.id: user.name for user in users["users"]}
    if query and not user_map:
        return {"total": 0, "results": []}
    # query db
    user_ids = list(user_map.keys()) if query else None
    results = CreditLogs.get_credit_log_by_page(
        user_ids=user_ids, offset=offset, limit=limit
    )
    total = CreditLogs.count_credit_log(user_ids=user_ids)
    # add username to results
    for result in results:
        setattr(result, "username", user_map.get(result.user_id, ""))
    return {"total": total, "results": results}


@router.post("/tickets", response_model=TradeTicketModel)
async def create_ticket(
    request: Request, form_data: dict, user: UserModel = Depends(get_verified_user)
) -> TradeTicketModel:
    out_trade_no = (
        f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"
    )
    if form_data["pay_type"] == "alipay" and ALIPAY_APP_ID.value:
        detail = await AlipayClient().create_trade(
            out_trade_no=out_trade_no, amount=form_data["amount"]
        )
    else:
        detail = await ezfp_client.create_trade(
            pay_type=form_data["pay_type"],
            out_trade_no=out_trade_no,
            amount=form_data["amount"],
            client_ip=request.client.host,
            ua=request.headers.get("User-Agent"),
        )
    return TradeTickets.insert_new_ticket(
        id=out_trade_no, user_id=user.id, amount=form_data["amount"], detail=detail
    )


@router.get("/callback", response_class=PlainTextResponse)
async def ticket_callback(request: Request) -> str:
    callback = dict(request.query_params)
    log.info("ezfp callback: %s", json.dumps(callback))
    if not ezfp_client.verify(callback):
        return "invalid signature"

    # payment failed
    if callback["trade_status"] != "TRADE_SUCCESS":
        return "success"

    # find ticket
    ticket = TradeTickets.get_ticket_by_id(callback["out_trade_no"])
    if not ticket:
        return "no ticket fount"

    # already callback
    if ticket.detail.get("callback"):
        return "success"

    ticket.detail["callback"] = callback
    TradeTickets.update_credit_by_id(ticket.id, ticket.detail)

    return "success"


@router.get("/callback/redirect", response_class=RedirectResponse)
async def ticket_callback_redirect() -> RedirectResponse:
    return RedirectResponse(url=EZFP_CALLBACK_HOST.value, status_code=302)


@router.post("/callback/alipay", response_class=PlainTextResponse)
async def alipay_callback(request: Request) -> str:
    callback = dict(await request.form())
    log.info("alipay callback: %s", json.dumps(callback))
    if not AlipayClient().verify(callback):
        return "invalid signature"

    # payment failed
    if callback["trade_status"] != "TRADE_SUCCESS":
        return "success"

    # find ticket
    ticket = TradeTickets.get_ticket_by_id(callback["out_trade_no"])
    if not ticket:
        return "no ticket fount"

    # already callback
    if ticket.detail.get("callback"):
        return "success"

    ticket.detail["callback"] = callback
    TradeTickets.update_credit_by_id(ticket.id, ticket.detail)

    return "success"


@router.get("/models/price")
async def get_model_price(request: Request, user: UserModel = Depends(get_admin_user)):
    # no info means not saved in db, which cannot be updated
    # preset model is always using base model's price
    return {
        model["id"]: model.get("info", {}).get("price") or {}
        for model in await get_all_models(request, user)
        if model.get("info") and not model.get("info", {}).get("base_model_id")
    }


@router.put("/models/price")
async def update_model_price(
    form_data: dict[str, dict], _: UserModel = Depends(get_admin_user)
):
    for model_id, price in form_data.items():
        model = Models.get_model_by_id(id=model_id)
        if not model:
            continue
        model.price = (
            ModelPriceForm.model_validate(price).model_dump() if price else None
        )
        Models.update_model_by_id(id=model_id, model=model)
    return f"success update price for {len(form_data)} models"


# Constants for model name formatting
MODEL_NAME_FORMATS = {
    'gpt': 'GPT', 'chatgpt': 'ChatGPT',
    'glm': 'GLM', 'deepseek': 'DeepSeek'
}

# Icons without color suffix
ICONS_WITHOUT_COLOR_SUFFIX = {
    'openai', 'grok', 'anthropic', 'mistral', 'cohere',
    'huggingface', 'meta', 'stability'
}

# CDN base URL for lobe-icons
LOBE_ICONS_CDN = "https://registry.npmmirror.com/@lobehub/icons-static-svg/latest/files/icons"


def convert_model_name_to_display(model_name: str) -> str:
    """Convert model_name to display name with special formatting rules."""
    words = model_name.replace('-', ' ').split()
    return ' '.join(MODEL_NAME_FORMATS.get(w.lower(), w.capitalize()) for w in words)


def convert_lobe_icon_to_url(icon_name: str) -> str:
    """Convert lobe-icons format to CDN URL."""
    if not icon_name or icon_name.startswith(('http://', 'https://', '/')):
        return icon_name
    
    import re
    match = re.match(r'^([A-Za-z0-9]+)\.(Color|Mono|Text)$', icon_name)
    if not match:
        return icon_name
    
    name, variant = match.groups()
    lower_name = name.lower()
    
    # Determine icon path based on variant
    if variant == 'Color':
        icon_path = lower_name if lower_name in ICONS_WITHOUT_COLOR_SUFFIX else f"{lower_name}-color"
    else:
        icon_path = f"{lower_name}-{variant.lower()}"
    
    return f"{LOBE_ICONS_CDN}/{icon_path}.svg"


def transform_pricing_data(pricing_data: dict) -> dict:
    """Transform external API pricing data to OpenWebUI format."""
    data_list = pricing_data.get("data", [])
    if not isinstance(data_list, list):
        return {}
    
    transformed = {}
    for model_data in data_list:
        model_name = model_data.get("model_name")
        if not model_name:
            continue
        
        # Extract and convert pricing (all per 1M tokens/requests)
        model_ratio = float(model_data.get("model_ratio", 0))
        price = {
            "prompt_price": model_ratio,
            "prompt_cache_price": model_ratio / 2,
            "completion_price": float(model_data.get("completion_ratio", 0)),
            "request_price": float(model_data.get("model_price", 0)) * 1000000,
            "minimum_credit": 0.01
        }
        
        # Build meta with tags and icon
        tags_str = model_data.get("tags", "")
        tags_list = [{"name": tag.strip()} for tag in tags_str.split(",") if tag.strip()] if tags_str else []
        
        meta = {
            "description": model_data.get("description", ""),
            "tags": tags_list,
            "profile_image_url": convert_lobe_icon_to_url(model_data.get("icon", ""))
        }
        
        transformed[model_name] = {
            "name": convert_model_name_to_display(model_name),
            "price": price,
            "meta": meta,
            "access_control": None
        }
    
    return transformed


def _get_pricing_url(base_url: str) -> str:
    """Convert base URL to pricing URL, removing /v1 suffix if present."""
    url = base_url.rstrip('/')
    return f"{url[:-3] if url.endswith('/v1') else url}/api/pricing"


def _get_meta_dict(meta) -> dict:
    """Convert meta to dict, handling both Pydantic models and dicts."""
    if not meta:
        return {}
    return meta.model_dump() if hasattr(meta, 'model_dump') else meta.copy() if isinstance(meta, dict) else {}


async def _fetch_pricing_from_url(session, url: str, api_key: str) -> tuple[dict | None, dict | None]:
    """Fetch pricing data from a single URL."""
    import aiohttp
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                data = await response.json()
                log.info(f"Successfully fetched pricing from {url}")
                return data, None
            else:
                error = {"url": url, "status": response.status, "error": await response.text()}
                log.warning(f"Failed to fetch pricing from {url}: HTTP {response.status}")
                return None, error
    except Exception as e:
        log.error(f"Error fetching pricing from {url}: {str(e)}")
        return None, {"url": url, "error": str(e)}


@router.post("/models/pricing/fetch")
async def fetch_pricing_from_openai(
    request: Request, user: UserModel = Depends(get_admin_user)
):
    """Fetch and update model pricing from configured OpenAI API endpoints."""
    import aiohttp
    from open_webui.models.models import ModelForm
    
    config = request.app.state.config
    all_pricing_data, errors, updated_models = [], [], []
    
    # Fetch pricing from all enabled connections
    async with aiohttp.ClientSession(trust_env=True) as session:
        for idx, base_url in enumerate(config.OPENAI_API_BASE_URLS):
            api_config = config.OPENAI_API_CONFIGS.get(str(idx), config.OPENAI_API_CONFIGS.get(base_url, {}))
            
            if not api_config.get("enable", True):
                continue
            
            api_key = config.OPENAI_API_KEYS[idx] if idx < len(config.OPENAI_API_KEYS) else ""
            pricing_url = _get_pricing_url(base_url)
            
            log.info(f"Fetching pricing from: {pricing_url}")
            data, error = await _fetch_pricing_from_url(session, pricing_url, api_key)
            
            if data:
                all_pricing_data.append(data)
            if error:
                errors.append(error)
    
    # Transform and update models
    for pricing_data in all_pricing_data:
        try:
            transformed_data = transform_pricing_data(pricing_data)
            log.info(f"Transformed {len(transformed_data)} models")
            
            for model_id, model_info in transformed_data.items():
                try:
                    existing_model = Models.get_model_by_id(id=model_id)
                    price_form = ModelPriceForm.model_validate(model_info["price"]).model_dump()
                    
                    if existing_model:
                        # Update existing model
                        existing_model.name = model_info["name"]
                        existing_model.price = price_form
                        existing_model.access_control = model_info.get("access_control")
                        
                        existing_meta = _get_meta_dict(existing_model.meta)
                        existing_meta.update(model_info["meta"])
                        existing_model.meta = existing_meta
                        
                        Models.update_model_by_id(id=model_id, model=existing_model)
                        updated_models.append({"id": model_id, "name": model_info["name"], "status": "updated"})
                    else:
                        # Create new model
                        new_model = ModelForm(
                            id=model_id,
                            name=model_info["name"],
                            base_model_id=None,
                            meta=model_info["meta"],
                            params={},
                            access_control=model_info.get("access_control"),
                            price=ModelPriceForm.model_validate(model_info["price"])
                        )
                        
                        if Models.insert_new_model(form_data=new_model, user_id=user.id):
                            updated_models.append({"id": model_id, "name": model_info["name"], "status": "created"})
                            
                except Exception as e:
                    log.error(f"Error updating model {model_id}: {str(e)}")
                    errors.append({"model_id": model_id, "error": str(e)})
                    
        except Exception as e:
            log.error(f"Error transforming pricing data: {str(e)}")
            errors.append({"error": f"Data transformation error: {str(e)}"})
    
    log.info(f"Pricing fetch completed: updated {len(updated_models)} model(s)")
    
    return {
        "success": bool(updated_models),
        "updated_models": updated_models,
        "total_updated": len(updated_models),
        "errors": errors or None,
        "message": f"Successfully updated {len(updated_models)} model(s)",
        "debug": {
            "total_api_calls": len(config.OPENAI_API_BASE_URLS),
            "successful_fetches": len(all_pricing_data),
            "total_errors": len(errors)
        }
    }


class StatisticRequest(BaseModel):
    start_time: int
    end_time: int


@router.post("/statistics")
async def get_statistics(
    form_data: StatisticRequest, _: UserModel = Depends(get_admin_user)
):
    # load credit data
    logs = CreditLogs.get_log_by_time(form_data.start_time, form_data.end_time)
    trade_logs = TradeTickets.get_ticket_by_time(
        form_data.start_time, form_data.end_time
    )

    # load user data
    users = Users.get_users()["users"]
    user_map = {user.id: user.name for user in users}

    # build graph data
    total_tokens = 0
    total_credit = 0
    model_cost_pie = defaultdict(int)
    model_token_pie = defaultdict(int)
    user_cost_pie = defaultdict(int)
    user_token_pie = defaultdict(int)
    for log in logs:
        if not log.detail.usage or log.detail.usage.total_price is None:
            continue

        model = log.detail.api_params.model
        if not model:
            continue

        total_tokens += log.detail.usage.total_tokens
        total_credit += log.detail.usage.total_price

        model_key = log.detail.api_params.model.id
        model_cost_pie[model_key] += log.detail.usage.total_price
        model_token_pie[model_key] += log.detail.usage.total_tokens

        user_key = f"{log.user_id}:{user_map.get(log.user_id, log.user_id)}"
        user_cost_pie[user_key] += log.detail.usage.total_price
        user_token_pie[user_key] += log.detail.usage.total_tokens

    # build trade data
    total_payment = 0
    user_payment_data = defaultdict(Decimal)
    for log in trade_logs:
        callback = log.detail.get("callback")
        if not callback:
            continue
        if callback.get("trade_status") != "TRADE_SUCCESS":
            continue
        time_key = datetime.datetime.fromtimestamp(log.created_at).strftime("%Y-%m-%d")
        user_payment_data[time_key] += log.amount
        total_payment += log.amount
    user_payment_stats_x = []
    user_payment_stats_y = []
    for key, val in user_payment_data.items():
        user_payment_stats_x.append(key)
        user_payment_stats_y.append(val)

    # response
    return {
        "total_tokens": total_tokens,
        "total_credit": total_credit,
        "model_cost_pie": [
            {"name": model, "value": total} for model, total in model_cost_pie.items()
        ],
        "model_token_pie": [
            {"name": model, "value": total} for model, total in model_token_pie.items()
        ],
        "user_cost_pie": [
            {"name": user.split(":", 1)[1], "value": total}
            for user, total in user_cost_pie.items()
        ],
        "user_token_pie": [
            {"name": user.split(":", 1)[1], "value": total}
            for user, total in user_token_pie.items()
        ],
        "total_payment": total_payment,
        "user_payment_stats_x": user_payment_stats_x,
        "user_payment_stats_y": user_payment_stats_y,
    }


@router.get("/redemption_codes")
async def get_redemption_codes(
    keyword: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    _: UserModel = Depends(get_admin_user),
) -> dict:
    """
    Get all redemption codes.
    """
    # init params
    page = page or 1
    limit = limit or PAGE_ITEM_COUNT
    offset = (page - 1) * limit
    # query codes
    try:
        keyword = int(keyword)
    except (ValueError, TypeError):
        pass
    total, codes = RedemptionCodes.get_codes(
        keyword=keyword, offset=offset, limit=limit
    )
    if not codes:
        return {"total": 0, "results": []}
    # query users
    users = Users.get_users_by_user_ids(user_ids={code.user_id for code in codes})
    user_map = {user.id: user.name for user in users}
    for code in codes:
        setattr(code, "username", user_map.get(code.user_id, ""))
    # response
    return {"total": total, "results": codes}


class CreateRedemptionCodeForm(BaseModel):
    purpose: str = Field(min_length=1, max_length=255)
    count: int = Field(ge=1, le=1000)
    amount: float = Field(gt=0)
    expired_at: Optional[int] = Field(default=None, gt=0)


@router.post("/redemption_codes")
async def create_redemption_code(
    form_data: CreateRedemptionCodeForm, _: UserModel = Depends(get_admin_user)
) -> dict:
    """
    Create redemption codes
    """
    now = int(time.time())
    if form_data.expired_at is not None:
        expired_at = datetime.datetime.fromtimestamp(form_data.expired_at)
        if expired_at.timestamp() < now:
            raise HTTPException(
                status_code=400, detail="Expiration time must be in the future."
            )
    codes = [
        RedemptionCodeModel(
            code=f"{uuid.uuid4().hex}{uuid.uuid1().hex}",
            purpose=form_data.purpose,
            amount=Decimal(form_data.amount),
            created_at=now,
            expired_at=form_data.expired_at,
        )
        for _ in range(form_data.count)
    ]
    RedemptionCodes.insert_codes(codes)
    return {"total": len(codes)}


class UpdateRedemptionCodeForm(BaseModel):
    purpose: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    expired_at: Optional[int] = Field(None, gt=0)


@router.put("/redemption_codes/{code}")
async def update_redemption_code(
    code: str,
    form_data: UpdateRedemptionCodeForm,
    _: UserModel = Depends(get_admin_user),
) -> None:
    """
    Update a redemption code
    """
    existing_code = RedemptionCodes.get_code(code)
    if not existing_code:
        raise HTTPException(status_code=404, detail="Redemption code not found.")

    if existing_code.received_at is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot update a code that has already been received.",
        )

    if form_data.expired_at is not None:
        expired_at = datetime.datetime.fromtimestamp(form_data.expired_at)
        if expired_at.timestamp() < int(time.time()):
            raise HTTPException(
                status_code=400, detail="Expiration time must be in the future."
            )

    existing_code.purpose = form_data.purpose
    existing_code.amount = Decimal(form_data.amount)
    existing_code.expired_at = form_data.expired_at

    return RedemptionCodes.update_code(existing_code)


@router.delete("/redemption_codes/{code}")
async def delete_redemption_codes(
    code: str, _: UserModel = Depends(get_admin_user)
) -> None:
    """
    Delete a redemption code
    """
    return RedemptionCodes.delete_code(code)


@router.get("/redemption_codes/export")
async def export_redemption_codes(
    keyword: str, _: UserModel = Depends(get_admin_user)
) -> Response:
    """
    Export all redemption codes as a plain text response.
    """
    _, codes = RedemptionCodes.get_codes(keyword=keyword)
    # build CSV content
    csv_content = "Code,Purpose,Amount,User ID,Created At,Expired At,Received At\n"
    for code in codes:
        csv_content += (
            ",".join(
                [
                    code.code,
                    f'"{code.purpose}"',
                    str(code.amount),
                    str(code.user_id) if code.user_id else "",
                    datetime.datetime.fromtimestamp(code.created_at).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    (
                        datetime.datetime.fromtimestamp(code.expired_at).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if code.expired_at
                        else ""
                    ),
                    (
                        datetime.datetime.fromtimestamp(code.received_at).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if code.received_at
                        else ""
                    ),
                ]
            )
            + "\n"
        )
    # set the response headers
    headers = {
        "Content-Disposition": f"attachment; filename={quote(keyword)}.csv",
        "Content-Type": "text/csv",
    }
    # return the response
    return Response(content=csv_content, headers=headers)


@router.get("/redemption_codes/{code}/receive")
async def receive_redemption_code(
    code: str, user: UserModel = Depends(get_verified_user)
) -> None:
    """
    Receive a redemption code.
    """
    RedemptionCodes.receive_code(code, user.id)
    return None
