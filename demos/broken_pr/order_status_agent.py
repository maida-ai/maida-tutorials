"""Deterministic order-status agent for the broken-PR regression demo."""

import argparse
import time

from maida import record_tool_call, trace


ORDER = {
    "order_id": "ORD-1042",
    "status": "shipped",
    "arrival_day": "Friday",
}


def lookup_order(order_id: str) -> dict[str, str]:
    """Return fixed local order data without network access."""
    if order_id != ORDER["order_id"]:
        raise LookupError(f"Unknown order: {order_id}")
    return ORDER.copy()


def compose_reply(order: dict[str, str]) -> str:
    """Turn the fixed order data into the customer-facing answer."""
    return (
        f"Order {order['order_id']} has {order['status']} "
        f"and will arrive {order['arrival_day']}."
    )


@trace(name="broken-pr-order-status")
def run_agent(lookups: int = 1) -> str:
    """Look up an order and return the same answer regardless of retry count."""
    order = ORDER
    for _ in range(lookups):
        order = lookup_order(ORDER["order_id"])
        record_tool_call(
            "lookup_order",
            args={"order_id": ORDER["order_id"]},
            result=order,
        )

    # Keep the baseline duration non-zero on fast machines and released Maida builds.
    time.sleep(0.02)
    reply = compose_reply(order)
    record_tool_call(
        "compose_reply",
        args={"order": order},
        result=reply,
    )
    return reply


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic Maida broken-PR demo agent."
    )
    parser.add_argument(
        "--lookups",
        type=int,
        default=1,
        help="number of identical order lookups to perform (default: 1)",
    )
    arguments = parser.parse_args()
    if arguments.lookups < 1:
        parser.error("--lookups must be at least 1")
    return arguments


def main() -> None:
    arguments = parse_args()
    print(run_agent(lookups=arguments.lookups))


if __name__ == "__main__":
    main()
