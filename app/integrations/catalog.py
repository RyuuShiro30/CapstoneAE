from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    """Public values from the authorized catalog, with None for unavailable fields."""

    price_idr_per_kg: int | None = None
    in_stock: bool | None = None

    def __post_init__(self) -> None:
        if self.price_idr_per_kg is not None and (
            type(self.price_idr_per_kg) is not int or self.price_idr_per_kg <= 0
        ):
            raise ValueError("Catalog price must be a positive integer in rupiah.")
        if self.in_stock is not None and not isinstance(self.in_stock, bool):
            raise ValueError("Catalog availability must be a boolean or None.")


class CatalogReader(Protocol):
    async def get_current_product(self) -> CatalogSnapshot | None:
        """Read the current, public product values from the authorized source."""
        ...
