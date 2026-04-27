"""Cost layer — converts token counts into USD and tenant currency.

* :class:`calculator.CostCalculator` — pure function over token counts and
  a :class:`pricing.resolver.PricingSnapshot`. Decimal precision.
* :class:`fx_resolver.FXResolver` — USD → tenant currency rate at a given
  date, cached daily, source ``api.frankfurter.dev``.
"""
