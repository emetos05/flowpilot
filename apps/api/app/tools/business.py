"""Read-only synthetic business fixtures for Day 3, not production customer data."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


CustomerId = Annotated[str, Field(pattern=r"^cus_[0-9]{3}$")]
OrderId = Annotated[str, Field(pattern=r"^ord_[0-9]{4}$")]
PolicyId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")]


class GetCustomerInput(ToolModel):
    customer_id: CustomerId


class GetOrderInput(ToolModel):
    order_id: OrderId


class GetRefundPolicyInput(ToolModel):
    policy_id: PolicyId


class Customer(ToolModel):
    customer_id: CustomerId
    name: str
    tier: Literal["standard", "premium"]


class Order(ToolModel):
    order_id: OrderId
    customer_id: CustomerId
    status: Literal["processing", "shipped", "delivered"]
    total_cents: int = Field(ge=0)
    currency: Literal["USD"]
    refund_policy_id: PolicyId


class RefundPolicy(ToolModel):
    policy_id: PolicyId
    return_window_days: int = Field(gt=0)
    conditions: tuple[str, ...]
    requires_human_approval: bool


class Found[T: BaseModel](ToolModel):
    status: Literal["found"] = "found"
    source: Literal["synthetic_demo"] = "synthetic_demo"
    record: T


class NotFound(ToolModel):
    status: Literal["not_found"] = "not_found"
    source: Literal["synthetic_demo"] = "synthetic_demo"


class BusinessTools:
    """Small fixture-backed adapter; business-table persistence belongs to Day 5."""

    def __init__(self):
        self._customers = {
            "cus_001": Customer(customer_id="cus_001", name="Maya Chen", tier="standard"),
            "cus_002": Customer(customer_id="cus_002", name="Leo Rivera", tier="premium"),
        }
        self._orders = {
            "ord_1001": Order(
                order_id="ord_1001",
                customer_id="cus_001",
                status="delivered",
                total_cents=7499,
                currency="USD",
                refund_policy_id="standard",
            ),
            "ord_1002": Order(
                order_id="ord_1002",
                customer_id="cus_002",
                status="shipped",
                total_cents=12900,
                currency="USD",
                refund_policy_id="standard",
            ),
        }
        self._policies = {
            "standard": RefundPolicy(
                policy_id="standard",
                return_window_days=30,
                conditions=(
                    "Request a return within 30 days of delivery.",
                    "Items must be unused and in their original packaging.",
                    "Shipping charges are not refundable unless the item is defective.",
                    "A human must verify eligibility and approve any refund.",
                ),
                requires_human_approval=True,
            )
        }

    def get_customer(self, arguments: GetCustomerInput) -> Found[Customer] | NotFound:
        arguments = GetCustomerInput.model_validate(arguments)
        record = self._customers.get(arguments.customer_id)
        return Found[Customer](record=record) if record else NotFound()

    def get_order(self, arguments: GetOrderInput) -> Found[Order] | NotFound:
        arguments = GetOrderInput.model_validate(arguments)
        record = self._orders.get(arguments.order_id)
        return Found[Order](record=record) if record else NotFound()

    def get_refund_policy(self, arguments: GetRefundPolicyInput) -> Found[RefundPolicy] | NotFound:
        arguments = GetRefundPolicyInput.model_validate(arguments)
        record = self._policies.get(arguments.policy_id)
        return Found[RefundPolicy](record=record) if record else NotFound()
