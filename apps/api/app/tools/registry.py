from typing import Literal

from pydantic import BaseModel, ValidationError

from app.tools.business import (
    BusinessTools,
    GetCustomerInput,
    GetOrderInput,
    GetRefundPolicyInput,
    ToolModel,
)


class ToolError(ToolModel):
    status: Literal["invalid_arguments", "unknown_tool"]
    message: str


class ToolRegistry:
    def __init__(self, business: BusinessTools | None = None):
        business = business or BusinessTools()
        # Dispatch only by a registered tool name, never by keywords in the user message.
        self._tools = {
            "get_customer": (
                GetCustomerInput,
                business.get_customer,
                "Read a synthetic demo customer profile by customer_id, e.g. cus_001. "
                "Use an ID supplied by the user or a previous tool result. Returns found or not_found.",
            ),
            "get_order": (
                GetOrderInput,
                business.get_order,
                "Read a synthetic demo order's status, total, customer ID and policy ID "
                "by order_id, e.g. ord_1001. Use an order ID supplied by the user or a previous tool result. Returns found or not_found.",
            ),
            "get_refund_policy": (
                GetRefundPolicyInput,
                business.get_refund_policy,
                "Look up return windows, return conditions, and refund rules from the synthetic "
                "demo refund policy. No customer or order ID is needed. "
                "Use policy_id standard for a general refund-policy question, or a supplied "
                "policy ID. Does not decide eligibility or issue a refund. Returns found or not_found.",
            ),
        }

    def definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "name": name,
                "description": description,
                "parameters": input_type.model_json_schema(),
                "strict": True,
            }
            for name, (input_type, _, description) in self._tools.items()
        ]

    def execute(self, name: str, arguments: str) -> BaseModel:
        tool = self._tools.get(name)
        if tool is None:
            return ToolError(status="unknown_tool", message="The requested tool is not available.")
        input_type, handler, _ = tool
        try:
            validated = input_type.model_validate_json(arguments)
        except ValidationError:
            return ToolError(
                status="invalid_arguments", message="Tool arguments do not match the schema."
            )
        return handler(validated)
