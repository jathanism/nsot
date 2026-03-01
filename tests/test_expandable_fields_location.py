"""
TDD: Verify that drf-flex-fields reads expandable_fields from Meta class.

This confirms that:
1. expandable_fields on Meta is preferred over class-level
2. The filter backend ONLY reads from Meta (not class-level)
3. Both locations work for the serializer mixin itself
"""

import pytest
from rest_flex_fields import FlexFieldsModelSerializer
from rest_flex_fields.filter_backends import FlexFieldsFilterBackend

from nsot.models import Site


class SiteSerializerClassLevel(FlexFieldsModelSerializer):
    """expandable_fields as class attribute (current NSoT pattern)."""

    expandable_fields = {
        "parent": (
            "tests.test_expandable_fields_location.SiteSerializerClassLevel",
            {},
        ),
    }

    class Meta:
        model = Site
        fields = ["id", "name"]


class SiteSerializerMetaLevel(FlexFieldsModelSerializer):
    """expandable_fields on Meta (recommended by drf-flex-fields)."""

    class Meta:
        model = Site
        fields = ["id", "name"]
        expandable_fields = {
            "parent": (
                "tests.test_expandable_fields_location.SiteSerializerMetaLevel",
                {},
            ),
        }


class SiteSerializerBothLevels(FlexFieldsModelSerializer):
    """expandable_fields on BOTH class and Meta — Meta should win."""

    expandable_fields = {
        "class_level_field": (
            "tests.test_expandable_fields_location.SiteSerializerClassLevel",
            {},
        ),
    }

    class Meta:
        model = Site
        fields = ["id", "name"]
        expandable_fields = {
            "meta_level_field": (
                "tests.test_expandable_fields_location.SiteSerializerMetaLevel",
                {},
            ),
        }


class TestExpandableFieldsLocation:
    """Test where drf-flex-fields looks for expandable_fields."""

    def test_class_level_works_for_serializer(self):
        """Serializer mixin reads class-level expandable_fields."""
        s = SiteSerializerClassLevel()
        assert "parent" in s._expandable_fields

    def test_meta_level_works_for_serializer(self):
        """Serializer mixin reads Meta-level expandable_fields."""
        s = SiteSerializerMetaLevel()
        assert "parent" in s._expandable_fields

    def test_meta_takes_priority_over_class(self):
        """When both are defined, Meta wins."""
        s = SiteSerializerBothLevels()
        assert "meta_level_field" in s._expandable_fields
        assert "class_level_field" not in s._expandable_fields

    def test_filter_backend_reads_meta_only(self):
        """FlexFieldsFilterBackend._get_expandable_fields only reads Meta."""
        # Meta-level: should work
        result = FlexFieldsFilterBackend._get_expandable_fields(
            SiteSerializerMetaLevel
        )
        assert "parent" in result

    def test_filter_backend_fails_without_meta(self):
        """FlexFieldsFilterBackend._get_expandable_fields fails if only class-level."""
        with pytest.raises(AttributeError):
            FlexFieldsFilterBackend._get_expandable_fields(
                SiteSerializerClassLevel
            )
