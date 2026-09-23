import json

import pytest
from pydantic import ValidationError

from app.tools.business import (
    BusinessTools,
    Customer,
    Found,
    GetCustomerInput,
    GetOrderInput,
    GetRefundPolicyInput,
    NotFound,
    Order,
    RefundPolicy,
)
from app.tools.registry import ToolError, ToolRegistry

CASES = [
    ("get_customer", GetCustomerInput, "customer_id", "cus_001", "cus_999", Customer),
    ("get_order", GetOrderInput, "order_id", "ord_1001", "ord_9999", Order),
    ("get_refund_policy", GetRefundPolicyInput, "policy_id", "standard", "missing", RefundPolicy),
]


@pytest.mark.parametrize(("name", "input_type", "field", "known", "missing", "output_type"), CASES)
def test_each_tool_returns_typed_record_and_not_found(
    name, input_type, field, known, missing, output_type
):
    handler = getattr(BusinessTools(), name)
    result = handler(input_type(**{field: known}))
    assert isinstance(result, Found[output_type])
    assert getattr(result.record, field) == known
    assert result.source == "synthetic_demo"
    assert isinstance(handler(input_type(**{field: missing})), NotFound)


@pytest.mark.parametrize(("name", "input_type", "field", "known", "missing", "output_type"), CASES)
@pytest.mark.parametrize("bad", [None, 42, "", "../private", [], " " * 5])
def test_invalid_input_cannot_reach_lookup(
    name, input_type, field, known, missing, output_type, bad
):
    with pytest.raises(ValidationError):
        getattr(BusinessTools(), name)({field: bad})


@pytest.mark.parametrize(("name", "input_type", "field", "known", "missing", "output_type"), CASES)
def test_registry_validates_and_dispatches(name, input_type, field, known, missing, output_type):
    registry = ToolRegistry()
    result = registry.execute(name, json.dumps({field: known}))
    assert isinstance(result, Found[output_type])
    for arguments in [
        "{}",
        "null",
        "[]",
        "not-json",
        json.dumps({field: known, "extra": "secret-marker"}),
    ]:
        error = registry.execute(name, arguments)
        assert isinstance(error, ToolError)
        assert error.status == "invalid_arguments"
        assert "secret-marker" not in error.model_dump_json()


def test_registry_cannot_invoke_unregistered_functions():
    for name in ["__init__", "__import__", "issue_refund", "get_customer.__globals__"]:
        result = ToolRegistry().execute(name, "{}")
        assert isinstance(result, ToolError)
        assert result.status == "unknown_tool"


def test_strict_tool_schemas_match_runtime_inputs():
    tools = ToolRegistry().definitions()
    assert {tool["name"] for tool in tools} == {case[0] for case in CASES}
    for tool in tools:
        assert tool["strict"] is True
        assert tool["parameters"]["additionalProperties"] is False
        assert set(tool["parameters"]["required"]) == set(tool["parameters"]["properties"])


def test_fixture_relations_and_read_only_records():
    business = BusinessTools()
    order = business.get_order(GetOrderInput(order_id="ord_1001")).record
    customer = business.get_customer(GetCustomerInput(customer_id=order.customer_id)).record
    policy = business.get_refund_policy(
        GetRefundPolicyInput(policy_id=order.refund_policy_id)
    ).record
    assert customer.name == "Maya Chen"
    assert order.total_cents == 7499
    assert policy.return_window_days == 30
    assert policy.requires_human_approval is True
    with pytest.raises(ValidationError):
        order.total_cents = 0
    assert business.get_order(GetOrderInput(order_id="ord_1001")).record.total_cents == 7499
