"""Tests for retargeting (MOFU) campaign filtering in ad providers."""
import pytest


class TestRetargetingFilter:
    """Tests for stage='nurturing' filtering across ad providers."""

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_meta_provider_nurturing_filters_custom_audiences(self):
        """MetaProvider with stage='nurturing' returns only adsets with custom_audiences."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_meta_provider_nurturing_uses_retargeting_slug(self):
        """MetaProvider with stage='nurturing' uses channel_slug='meta-retargeting'."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_google_ads_provider_nurturing_filters_remarketing(self):
        """GoogleAdsProvider with stage='nurturing' filters to UserList criterion."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_tiktok_provider_nurturing_filters_custom_audiences(self):
        """TikTokProvider with stage='nurturing' filters to Custom Audiences."""
        pass
