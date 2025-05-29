import json
import logging
import time
from decimal import Decimal
from typing import List, Union

import tiktoken
from fastapi import HTTPException
from tiktoken import Encoding

from open_webui.config import (
    USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE,
    USAGE_DEFAULT_ENCODING_MODEL,
    USAGE_CALCULATE_MINIMUM_COST,
)
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.credits import AddCreditForm, Credits, SetCreditFormDetail
from open_webui.models.models import Models
from open_webui.models.users import UserModel
from open_webui.utils.credit.models import (
    MessageContent,
    CompletionUsage,
    ChatCompletion,
    ChatCompletionChunk,
    MessageItem,
)
from open_webui.utils.credit.utils import (
    get_model_price,
    get_feature_price,
    calculate_image_token,
)

logger = logging.getLogger(__name__)
logger.setLevel(SRC_LOG_LEVELS["MAIN"])


class Calculator:
    """
    Usage Calculator
    """

    def __init__(self) -> None:
        self._encoder = {}

    def get_encoder(
        self,
        model_id: str,
        model_prefix_to_remove: str = "",
        default_model_for_encoding: str = "gpt-4o",
    ) -> Encoding:
        # remove prefix
        model_id_ops = model_id
        if model_prefix_to_remove:
            model_id_ops = model_id.lstrip(model_prefix_to_remove)
        # load from cache
        if model_id_ops in self._encoder:
            return self._encoder[model_id_ops]
        # load from tiktoken
        try:
            self._encoder[model_id_ops] = tiktoken.encoding_for_model(model_id_ops)
        except KeyError:
            return self.get_encoder(default_model_for_encoding)
        return self.get_encoder(model_id)

    def calculate_usage(
        self,
        cached_usage: CompletionUsage,
        model_id: str,
        messages: List[dict],
        response: Union[ChatCompletion, ChatCompletionChunk],
        model_prefix_to_remove: str = "",
        default_model_for_encoding: str = "gpt-4o",
    ) -> (bool, CompletionUsage):
        try:
            # use provider usage
            if response.usage is not None:
                return True, response.usage

            # init
            usage = CompletionUsage(
                prompt_tokens=0, completion_tokens=0, total_tokens=0
            )
            encoder = self.get_encoder(
                model_id=model_id,
                model_prefix_to_remove=model_prefix_to_remove,
                default_model_for_encoding=default_model_for_encoding,
            )

            # prompt tokens
            # only calculate once
            if cached_usage.prompt_tokens:
                usage.prompt_tokens = cached_usage.prompt_tokens
            else:
                for message in [
                    MessageItem.model_validate(message) for message in messages
                ]:
                    if isinstance(message.content, str):
                        usage.prompt_tokens += len(
                            encoder.encode(message.content or "")
                        )
                    if isinstance(message.content, list):
                        for item in message.content:
                            item: MessageContent
                            if item.type == "text":
                                usage.prompt_tokens += len(
                                    encoder.encode(item.text or "")
                                )
                            elif item.type == "image_url":
                                usage.prompt_tokens += calculate_image_token(
                                    model_id, item.image_url
                                )

            # completion tokens
            choices = response.choices
            if choices:
                choice = choices[0]
                if isinstance(response, ChatCompletion):
                    usage.completion_tokens = len(
                        encoder.encode(choice.message.content or "")
                    )
                elif isinstance(response, ChatCompletionChunk):
                    usage.completion_tokens = len(
                        encoder.encode(choice.delta.content or "")
                    )

            # total tokens
            usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
            return False, usage
        except Exception as err:
            logger.exception("[calculate_usage] failed: %s", err)
            raise err


calculator = Calculator()


class CreditDeduct:
    """
    Deduct Credit

    Must be used as following, so __exit__ will be called on exit

    with CreditDeduct(xxx) as credit_deduct:
        credit_deduct.run(xxx)
    """

    def __init__(
        self,
        user: UserModel,
        model_id: str,
        body: dict,
        is_stream: bool,
        is_embedding: bool = False,
    ) -> None:
        self.remote_id = ""
        self.user = user
        self.model_id = model_id
        self.model = Models.get_model_by_id(self.model_id)
        self.body = body
        self.is_stream = is_stream
        self.usage = CompletionUsage(
            prompt_tokens=0, completion_tokens=0, total_tokens=0
        )
        (
            self.prompt_unit_price,
            self.completion_unit_price,
            self.request_unit_price,
            _,
        ) = get_model_price(model=self.model, is_embedding=is_embedding)
        self.features = {
            k
            for k, v in (
                body.get("metadata", {}).get("features_for_credit", {}) or {}
            ).items()
            if v
        }
        self.is_official_usage = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Credits.add_credit_by_user_id(
            form_data=AddCreditForm(
                user_id=self.user.id,
                amount=Decimal(-self.total_price),
                detail=SetCreditFormDetail(
                    usage={
                        "total_price": float(self.total_price),
                        "prompt_unit_price": float(self.prompt_unit_price),
                        "completion_unit_price": float(self.completion_unit_price),
                        "request_unit_price": float(self.request_unit_price),
                        "feature_price": float(self.feature_price),
                        "features": list(self.features),
                        **self.usage.model_dump(exclude_unset=True, exclude_none=True),
                    },
                    api_params={
                        "model": (
                            self.model.model_dump(exclude_unset=True, exclude_none=True)
                            if self.model
                            else {"id": self.model_id}
                        ),
                        "is_stream": self.is_stream,
                    },
                    desc=f"updated by {self.__class__.__name__}",
                ),
            )
        )
        logger.info(
            "[credit_deduct] user: %s; model: %s; tokens: %d %d; cost: %s",
            self.user.name,
            self.model_id,
            self.usage.prompt_tokens,
            self.usage.completion_tokens,
            self.total_price,
        )

    @property
    def prompt_price(self) -> Decimal:
        return self.prompt_unit_price * self.usage.prompt_tokens / 1000 / 1000

    @property
    def completion_price(self) -> Decimal:
        return self.completion_unit_price * self.usage.completion_tokens / 1000 / 1000

    @property
    def request_price(self) -> Decimal:
        return self.request_unit_price / 1000 / 1000

    @property
    def feature_price(self) -> Decimal:
        return get_feature_price(self.features)

    @property
    def total_price(self) -> Decimal:
        if self.request_unit_price > 0:
            total_price = self.request_price + self.feature_price
        else:
            total_price = self.prompt_price + self.completion_price + self.feature_price
        return max(total_price, Decimal(USAGE_CALCULATE_MINIMUM_COST.value))

    def add_usage_to_resp(self, response: dict) -> dict:
        if not isinstance(response, dict):
            return response
        response["usage"] = self.usage_with_cost
        return response

    @property
    def usage_with_cost(self) -> dict:
        return {
            "total_cost": float(self.total_price),
            "cost_detail": {
                "prompt_price": float(self.prompt_price),
                "completion_price": float(self.completion_price),
                "request_price": float(self.request_price),
                "feature_price": float(self.feature_price),
                "is_calculate": not self.is_official_usage,
            },
            **self.usage.model_dump(exclude_unset=True, exclude_none=True),
        }

    @property
    def usage_message(self) -> str:
        return "data: %s\n\n" % json.dumps(
            {
                "id": self.remote_id,
                "created": int(time.time()),
                "model": self.model_id,
                "choices": [],
                "object": (
                    "chat.completion.chunk" if self.is_stream else "chat.completion"
                ),
                "usage": self.usage_with_cost,
            }
        )

    def run(self, response: Union[dict, bytes, str]) -> None:
        try:
            self._run(response)
        except Exception as e:
            logger.warning("[credit_deduct_failed] unknown error %s", e)

    def _run(self, response: Union[dict, bytes, str]) -> None:
        if not isinstance(response, (dict, bytes, str)):
            logger.warning("[credit_deduct] response is type of %s", type(response))
            return

        # prompt messages
        messages = self.body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="prompt messages is empty")

        # stream
        if self.is_stream:
            _response = self.clean_response(
                response=response,
                default_response={
                    "choices": [{"delta": {"content": self.to_str(response)}}],
                },
            )
            if not _response:
                return
            # validate
            response = ChatCompletionChunk.model_validate(_response)

        # non-stream
        else:
            _response = self.clean_response(
                response=response,
                default_response={
                    "choices": [{"message": {"content": self.to_str(response)}}],
                },
            )
            if not _response:
                return
            # validate
            response = ChatCompletion.model_validate(_response)

        # record is
        self.remote_id = getattr(response, "id", "")

        # calculate
        is_official_usage, usage = calculator.calculate_usage(
            cached_usage=self.usage,
            model_id=self.model_id,
            messages=messages,
            response=response,
            model_prefix_to_remove=USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE.value,
            default_model_for_encoding=USAGE_DEFAULT_ENCODING_MODEL.value,
        )
        if is_official_usage:
            self.is_official_usage = True
            self.usage = usage
            return
        if self.is_official_usage:
            return
        if self.is_stream:
            self.usage.prompt_tokens = usage.prompt_tokens
            self.usage.completion_tokens += usage.completion_tokens
            self.usage.total_tokens = (
                self.usage.prompt_tokens + self.usage.completion_tokens
            )
            return
        self.usage = usage

    def clean_response(
        self, response: Union[dict, bytes, str], default_response: dict
    ) -> dict:
        # dict
        if isinstance(response, dict):
            return response
        # str or bytes
        if isinstance(response, bytes):
            _response = response.decode("utf-8")
        else:
            _response = response
        # remove prefix
        _response = _response.strip().lstrip("data: ")
        if _response.startswith("[DONE]") or not _response:
            return {}
        try:
            _response = json.loads(_response)
        except json.decoder.JSONDecodeError:
            _response = default_response
        return _response

    def to_str(self, data: any) -> str:
        if isinstance(data, str):
            return data.strip()
        if isinstance(data, bytes):
            return data.decode("utf-8").strip()
        return str(data)
