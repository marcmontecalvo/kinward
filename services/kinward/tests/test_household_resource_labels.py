from kinward.domain.household_resource_labels import resolve_label, technical_reference


def test_resolve_label_prefers_an_explicit_override() -> None:
    assert (
        resolve_label(
            "light.office", override="Office Light", attributes={"friendly_name": "Some Light"}
        )
        == "Office Light"
    )


def test_resolve_label_falls_back_to_ha_friendly_name_without_an_override() -> None:
    assert (
        resolve_label("light.office", override=None, attributes={"friendly_name": "Office Light"})
        == "Office Light"
    )


def test_resolve_label_treats_a_blank_override_as_absent() -> None:
    """An 'invalid mapping' (empty/whitespace override) fails safely into the next tier
    rather than displaying nothing (Story 7.1)."""
    assert (
        resolve_label("light.office", override="   ", attributes={"friendly_name": "Office Light"})
        == "Office Light"
    )


def test_resolve_label_falls_back_to_the_raw_entity_id_as_a_last_resort() -> None:
    assert resolve_label("light.office", override=None, attributes=None) == "light.office"
    assert resolve_label("light.office", override="", attributes={}) == "light.office"
    assert (
        resolve_label("light.office", override=None, attributes={"friendly_name": "   "})
        == "light.office"
    )


def test_technical_reference_always_returns_the_raw_entity_id() -> None:
    assert technical_reference("light.office") == "light.office"
