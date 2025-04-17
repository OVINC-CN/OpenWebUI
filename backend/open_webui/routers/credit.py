import datetime
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from open_webui.config import EZFP_CALLBACK_HOST
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.credits import (
    TradeTicketModel,
    TradeTickets,
    CreditLogSimpleModel,
    CreditLogs,
)
from open_webui.models.models import Models, ModelPriceForm
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.utils.credit.ezfp import ezfp_client

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()


@router.get("/logs", response_model=list[CreditLogSimpleModel])
async def list_credit_logs(
    page: Optional[int] = None, user: UserModel = Depends(get_verified_user)
) -> TradeTicketModel:
    if page:
        limit = 100
        offset = (page - 1) * limit
        return CreditLogs.get_credit_log_by_user_id(
            user_id=user.id, offset=offset, limit=limit
        )
    else:
        return CreditLogs.get_credit_log_by_user_id(
            user_id=user.id, offset=0, limit=100
        )


@router.post("/tickets", response_model=TradeTicketModel)
async def create_ticket(
    request: Request, form_data: dict, user: UserModel = Depends(get_verified_user)
) -> TradeTicketModel:
    out_trade_no = (
        f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{uuid.uuid4().hex}"
    )
    return TradeTickets.insert_new_ticket(
        id=out_trade_no,
        user_id=user.id,
        amount=form_data["amount"],
        detail=await ezfp_client.create_trade(
            pay_type=form_data["pay_type"],
            out_trade_no=out_trade_no,
            amount=form_data["amount"],
            client_ip=request.client.host,
            ua=request.headers.get("User-Agent"),
        ),
    )


@router.get("/callback", response_class=PlainTextResponse)
async def ticket_callback(request: Request) -> str:
    callback = dict(request.query_params)
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


@router.get("/models/price")
async def get_model_price(_: UserModel = Depends(get_admin_user)):
    return {
        model.id: model.price if model.price else {}
        for model in Models.get_all_models()
        if model.id
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
