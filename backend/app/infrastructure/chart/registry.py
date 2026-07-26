"""Strategy registry for chart builders with automatic builder discovery."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import ClassVar, cast

from app.application.interfaces.i_chart_builder import IChartBuilder
from app.domain.enums import ChartType
from app.domain.exceptions import ChartValidationError
from app.infrastructure.chart.builders.base import BaseChartBuilder


class ChartBuilderRegistry:
    """Strategy registry maintaining chart builder instances keyed by ChartType.

    Enables Open-Closed principle: new chart builders (Scatter, Heatmap,
    Histogram, Treemap, Funnel, Sankey) can be registered at runtime without
    modifying existing builders or registry implementation.
    """

    _registry: ClassVar[dict[ChartType, IChartBuilder]] = {}
    _initialized: ClassVar[bool] = False

    @classmethod
    def register(cls, chart_type: ChartType | str, builder: IChartBuilder) -> None:
        """Register a builder strategy for a given ChartType."""
        ct = (
            ChartType.from_str(chart_type)
            if isinstance(chart_type, str)
            else chart_type
        )
        cls._registry[ct] = builder

    @classmethod
    def get(cls, chart_type: ChartType | str) -> IChartBuilder:
        """Retrieve the registered IChartBuilder strategy for a ChartType.

        Raises:
            ChartValidationError: If no builder strategy is registered.
        """
        cls.ensure_initialized()
        try:
            ct = (
                ChartType.from_str(chart_type)
                if isinstance(chart_type, str)
                else chart_type
            )
        except ValueError as exc:
            raise ChartValidationError(f"Unsupported chart type: {chart_type}") from exc

        builder = cls._registry.get(ct)
        if not builder:
            raise ChartValidationError(
                f"No chart builder strategy registered for chart type '{ct.value}'."
            )
        return builder

    @classmethod
    def supported_types(cls) -> list[ChartType]:
        """List all currently registered supported chart types."""
        cls.ensure_initialized()
        return list(cls._registry.keys())

    @classmethod
    def ensure_initialized(cls) -> None:
        """Lazy-initialize default chart builders if not yet initialized."""
        if not cls._initialized:
            cls._auto_register_builders()
            cls._initialized = True

    @classmethod
    def _auto_register_builders(cls) -> None:
        """Discover and register all concrete chart builders automatically."""
        builders_pkg = importlib.import_module("app.infrastructure.chart.builders")
        for module_info in pkgutil.iter_modules(
            builders_pkg.__path__, f"{builders_pkg.__name__}."
        ):
            if module_info.name.endswith(".base"):
                continue
            importlib.import_module(module_info.name)

        for builder_cls in BaseChartBuilder.__subclasses__():
            if inspect.isabstract(builder_cls):
                continue
            concrete_builder_cls = cast(type[IChartBuilder], builder_cls)
            builder = concrete_builder_cls()
            cls.register(builder.chart_type, builder)

    @classmethod
    def reset(cls) -> None:
        """Reset registry state (primarily for testing)."""
        cls._registry.clear()
        cls._initialized = False
