import logging

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
from alipay.aop.api.request.AlipayTradePrecreateRequest import (
    AlipayTradePrecreateRequest,
)
from alipay.aop.api.response.AlipayTradePrecreateResponse import (
    AlipayTradePrecreateResponse,
)
from alipay.aop.api.util.SignatureUtils import verify_with_rsa

from open_webui.config import (
    ALIPAY_SERVER_URL,
    ALIPAY_APP_ID,
    ALIPAY_APP_PRIVATE_KEY,
    ALIPAY_ALIPAY_PUBLIC_KEY,
    ALIPAY_AMOUNT_CONTROL,
    WEBUI_NAME,
)
from open_webui.env import SRC_LOG_LEVELS
from open_webui.utils.credit.utils import check_amount

logger = logging.getLogger(__name__)
logger.setLevel(SRC_LOG_LEVELS["MAIN"])


class AlipayClient:
    """
    alipay client
    """

    def __init__(self):
        self._client_config = AlipayClientConfig()
        self._client_config.server_url = ALIPAY_SERVER_URL.value
        self._client_config.app_id = ALIPAY_APP_ID.value
        self._client_config.app_private_key = ALIPAY_APP_PRIVATE_KEY.value
        self._client_config.alipay_public_key = ALIPAY_ALIPAY_PUBLIC_KEY.value
        self._client = DefaultAlipayClient(self._client_config, logger)

    def verify(self, payload: dict) -> bool:
        sign = payload.get("sign", "")
        if not sign:
            return False
        payload_filtered = [
            f"{k}={v}" for k, v in payload.items() if k not in ["sign", "sign_type"]
        ]
        payload_filtered.sort()
        payload_content = "&".join(payload_filtered)
        try:
            return verify_with_rsa(
                self._client_config.alipay_public_key, payload_content, sign
            )
        except Exception as err:
            logger.exception("alipay verify error: %s", err)
            return False

    async def create_trade(self, out_trade_no: str, amount: float) -> dict:
        # check for amount
        if not check_amount(amount, ALIPAY_AMOUNT_CONTROL.value):
            return {
                "code": -1,
                "msg": f"amount invalid, allows {' '.join(ALIPAY_AMOUNT_CONTROL.value.split(','))}",
            }
        # build request
        request_model = AlipayTradePrecreateModel()
        request_model.out_trade_no = out_trade_no
        request_model.total_amount = f"{amount:.2f}"
        request_model.subject = f"{WEBUI_NAME} Credit"
        request = AlipayTradePrecreateRequest(biz_model=request_model)
        # do request
        try:
            response_content = self._client.execute(request)
            response = AlipayTradePrecreateResponse()
            response.parse_response_content(response_content)
            if response.is_success():
                return {
                    "code": 1,
                    "trade_no": response.out_trade_no,
                    "qrcode": response.qr_code,
                }
            return {"code": -1, "msg": str(response_content)}
        except Exception as err:
            logger.exception("alipay create trade error: %s", err)
            return {"code": -1, "msg": str(err)}
