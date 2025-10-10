"""EC2 pricing lookup — on-demand hourly costs by instance type."""

# Hardcoded us-east-1 on-demand prices (updated Apr 2026)
# Source: https://aws.amazon.com/ec2/pricing/on-demand/
INSTANCE_PRICING: dict[str, float] = {
    "g4dn.xlarge": 0.526,
    "g4dn.2xlarge": 0.752,
    "g4dn.12xlarge": 3.912,
    "g5.xlarge": 1.006,
    "g5.2xlarge": 1.212,
    "g5.12xlarge": 5.672,
    "g5.48xlarge": 16.288,
    "g6e.xlarge": 1.168,
    "g6e.12xlarge": 7.008,
    "p4d.24xlarge": 32.773,
    "p5.48xlarge": 98.32,
    "inf2.xlarge": 0.758,
    "inf2.8xlarge": 1.968,
    "inf2.48xlarge": 12.981,
}


def get_hourly_cost(instance_type: str) -> float:
    """Get on-demand hourly cost for an instance type.

    Returns 0.0 if instance type is not in the pricing table.
    """
    return INSTANCE_PRICING.get(instance_type, 0.0)
