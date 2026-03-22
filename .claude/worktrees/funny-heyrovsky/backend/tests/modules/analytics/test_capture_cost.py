import pytest
from uuid import uuid4


class TestCaptureCostService:
    """Tests for cost configuration and calculation."""

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_get_channel_costs_sums_multiple_entries(self):
        """Multiple cost entries per channel (platform+agency+tool) are summed."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_get_channel_costs_filters_by_tenant(self):
        """Cost queries are tenant-isolated."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_prorated_agency_costs_distribute_evenly(self):
        """Agency costs with proration_category distribute across connected channels."""
        pass
