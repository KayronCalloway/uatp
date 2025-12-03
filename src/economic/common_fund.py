"""
Common Attribution Fund

Implements UATP's collective value preservation system:
1. Collects 10% of all dividend allocations
2. Distributes funds for public goods and diffuse contributions
"""


class CommonAttributionFund:
    def __init__(self):
        self.balance = 0.0

    def allocate(self, dividends: dict) -> dict:
        """
        Deduct 10% from total dividends for common fund
        and redistribute remaining 90% to contributors
        """
        total_value = sum(dividends.values())
        common_allocation = total_value * 0.1
        self.balance += common_allocation

        # Reduce individual allocations
        reduction_factor = 0.9
        return {
            entity: amount * reduction_factor for entity, amount in dividends.items()
        }
