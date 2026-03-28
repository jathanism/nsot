# Proposal: ASN Resource Type (#48)

> **Issue:** [jathanism/nsot#48](https://github.com/jathanism/nsot/issues/48) / [dropbox/nsot#148](https://github.com/dropbox/nsot/issues/148)
> **Status:** Draft — requesting design feedback
> **Author:** ClawdBot, with direction from @jathanism

---

## Background

The [original feature request](https://github.com/dropbox/nsot/issues/148) from @coxley identified a gap: users were already storing ASN data as opaque string attributes (e.g., `asn=65001` on networks), but had no way to describe *what* an ASN represents or query bidirectionally ("what is this ASN?" / "what originates from it?").

This is the classic attribute → first-class resource promotion pattern.

---

## Competitive Analysis

### NetBox (`netbox-community/netbox`)

NetBox treats ASN as a **standalone IPAM object** with rich relationships:

| Aspect | Implementation |
|--------|---------------|
| **Model** | `ipam.ASN` — inherits `PrimaryModel` (id, tags, custom fields, comments, description) |
| **Fields** | `asn` (BigIntegerField, unique globally), `rir` (required FK to RIR), `tenant` (optional FK) |
| **Relationships** | M2M to **Site** and **Provider** — a site can have multiple ASNs, an ASN can span sites |
| **ASN Ranges** | Separate `ASNRange` model with start/end, `get_available_asns()` for allocation |
| **BGP** | No built-in BGP model — ASN is reference data consumed by plugins |
| **Display** | `ASNField` (BigIntegerField + validators), ASDOT notation as computed property |
| **Scope** | Global uniqueness — ASN is unique across all tenants/sites |

**Key design choice:** ASN is globally unique (not per-site). RIR is *required*. M2M relationships to Site and Provider enable "this site uses these ASNs" and "this provider operates these ASNs."

**ASN Range** is a first-class model with allocation support (`get_available_asns()` returns set difference of range minus existing ASNs).

### Nautobot BGP Models (`nautobot-app-bgp-models`)

Nautobot takes a more **prescriptive, BGP-centric** approach:

| Aspect | Implementation |
|--------|---------------|
| **Model** | `AutonomousSystem` — inherits `PrimaryModel` (UUID, tags, custom fields, status) |
| **Fields** | `asn` (ASNField from core, unique globally), `description`, `provider` (optional FK), `status` |
| **Relationships** | FK from `BGPRoutingInstance` → ASN (required — ties ASN to a Device) |
| **BGP hierarchy** | `AutonomousSystem` → `BGPRoutingInstance` → `PeerGroup` → `PeerEndpoint` |
| **Inheritance** | Property inheritance system — ASN cascades down: RoutingInstance → PeerGroupTemplate → PeerGroup → PeerEndpoint |
| **Extra attributes** | JSONField with `deepmerge` inheritance for vendor-specific config knobs |
| **ASN Ranges** | `AutonomousSystemRange` with `get_next_available_asn()` |

**Key design choice:** ASN connects to devices *only through* `BGPRoutingInstance` — there's no direct ASN↔Site or ASN↔Device relationship. The 4-level property inheritance system mirrors how real BGP configs work (neighbor inherits from peer-group inherits from template).

**The app is opinionated:** it models BGP concepts (routing instances, peer groups, address families) as first-class Django models, not just attributes.

### Comparison Summary

| Feature | NetBox | Nautobot | NSoT (proposed) |
|---------|--------|----------|-----------------|
| ASN uniqueness | Global | Global | **Per-site** |
| RIR required? | Yes | No | **No** |
| Site relationship | M2M | Via BGPRoutingInstance | **FK (site)** |
| Device relationship | None direct | Via BGPRoutingInstance | **Via Protocol** |
| BGP modeling | Plugin territory | Full built-in hierarchy | **Via existing Protocol model** |
| ASN ranges | Yes (separate model) | Yes (separate model) | **Not in v1** |
| Attribute system | Custom fields | Custom fields + JSON | **EAV (existing Resource pattern)** |
| Complexity | Medium | High | **Low (intentionally)** |

---

## Proposed Design for NSoT

### Philosophy

Stay simple. NSoT's strength is its flexible EAV attribute system — we don't need to model every BGP concept as a Django model. ASN should be a **lightweight, first-class resource** that integrates naturally with the existing Protocol model.

### Naming

Following Jathan's feedback on avoiding `ASN.asn` redundancy:

- **Model class:** `AutonomousSystem`
- **Number field:** `AutonomousSystem.number`
- **API endpoint:** `/api/sites/:site_pk/autonomous_systems/`
- **String representation:** `AS65001`
- **`resource_name`:** `"AutonomousSystem"` (for attributes/values)

### Model: `AutonomousSystem`

```python
class AutonomousSystem(Resource):
    """Represents an Autonomous System Number (ASN)."""

    number = models.PositiveIntegerField(
        null=False,
        db_index=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(4294967294),  # Strict IANA: exclude 0 and 2^32-1
        ],
        help_text="The Autonomous System Number (1-4294967294).",
    )
    description = models.CharField(
        max_length=255,
        default="",
        blank=True,
        null=False,
        help_text="A description of what this Autonomous System represents.",
    )
    site = models.ForeignKey(
        "Site",
        db_index=True,
        related_name="autonomous_systems",
        on_delete=models.PROTECT,
        verbose_name="Site",
        help_text="Unique ID of the Site this Autonomous System is under.",
    )

    class Meta:
        unique_together = ("site", "number")
        verbose_name = "Autonomous System"
        verbose_name_plural = "Autonomous Systems"

    def __str__(self):
        return "AS%d" % self.number

    @property
    def number_asdot(self):
        """Return ASDOT notation for 32-bit ASNs (RFC 5396)."""
        if self.number >= 65536:
            hi, lo = divmod(self.number, 65536)
            return "%d.%d" % (hi, lo)
        return str(self.number)
```

**Inherits from Resource:** gets `_attributes_cache`, `expires_at`, `get_attributes()`, `set_attributes()`, `get_merged_attributes()`, and the full EAV attribute system for free.

### ASN Range Validation

Strict IANA range per Jathan's direction:
- **Minimum:** 1 (AS0 is reserved per [RFC 7607](https://datatracker.ietf.org/doc/html/rfc7607))
- **Maximum:** 4294967294 (AS4294967295 / AS65535.65535 is reserved per [RFC 7300](https://datatracker.ietf.org/doc/html/rfc7300))
- **Private ranges** (64512–65534 for 16-bit, 4200000000–4294967294 for 32-bit): allowed but could be flagged via attributes

### Integration with Protocol Model

The existing Protocol model already has `device`, `type` (ProtocolType), `interface`, and `circuit` FKs. For BGP protocol instances, ASN is a natural addition:

```python
# On Protocol model — optional FK
autonomous_system = models.ForeignKey(
    "AutonomousSystem",
    null=True,
    blank=True,
    db_index=True,
    related_name="protocols",
    on_delete=models.PROTECT,
    help_text="The Autonomous System associated with this protocol instance.",
)
```

This enables:
- **"What protocols use ASN 65001?"** → `Protocol.objects.filter(autonomous_system__number=65001)`
- **"What ASN does this BGP session use?"** → `protocol.autonomous_system`
- **"What devices run this ASN?"** → `Device.objects.filter(interfaces__protocols__autonomous_system=asn)`

**Not adding:** separate `local_asn` / `remote_asn` fields on Protocol. That level of BGP specificity is better handled via Protocol attributes (e.g., `local_asn=65001`, `remote_asn=65002`). If we later need richer BGP modeling, we can add it — but let's not over-model for v1.

### What We're NOT Building (v1)

| Feature | Why not |
|---------|---------|
| **ASN Ranges** | Useful but not essential for v1. Can add later as a separate model. |
| **RIR model** | NetBox requires this; we don't. RIR can be an attribute (`rir=ARIN`). |
| **Global uniqueness** | NSoT scopes everything per-site. Same ASN in different sites is valid (e.g., lab vs prod). |
| **M2M to Site** | NSoT uses FK to Site, not M2M. Consistent with all other resources. |
| **BGP session/peering models** | Protocol + ProtocolType + attributes handle this. Don't out-Nautobot Nautobot. |

### API

```
GET    /api/sites/1/autonomous_systems/          # List
POST   /api/sites/1/autonomous_systems/          # Create
GET    /api/sites/1/autonomous_systems/65001/     # Retrieve by natural key
PUT    /api/sites/1/autonomous_systems/65001/     # Update
PATCH  /api/sites/1/autonomous_systems/65001/     # Partial update
DELETE /api/sites/1/autonomous_systems/65001/     # Delete

# Also available at top-level
GET    /api/autonomous_systems/                   # List all
GET    /api/autonomous_systems/65001/             # Retrieve
```

**Filters:** `number`, `description`, `attributes`, `expired`, `expires_before`, `expires_after`

**Response shape:**
```json
{
    "id": 1,
    "number": 65001,
    "number_asdot": "65001",
    "description": "Production backbone",
    "site_id": 1,
    "attributes": {
        "region": "us-west",
        "rir": "ARIN",
        "type": "private"
    },
    "expires_at": null
}
```

### Files to Touch

| File | Changes |
|------|---------|
| `nsot/models/autonomous_system.py` | **New** — AutonomousSystem model |
| `nsot/models/__init__.py` | Import + `__all__` + signal |
| `nsot/models/constants.py` | Add to `RESOURCE_BY_IDX`, `VALID_ATTRIBUTE_RESOURCES` |
| `nsot/api/serializers.py` | 4 serializers (read, create, partial update, update) |
| `nsot/api/filters.py` | `AutonomousSystemFilter` |
| `nsot/api/views.py` | `AutonomousSystemViewSet` |
| `nsot/api/urls.py` | Register on both routers |
| `nsot/models/protocol.py` | Add optional `autonomous_system` FK |
| `nsot/api/serializers.py` | Update Protocol serializers for new FK |
| `nsot/migrations/` | 1-2 new migrations |
| `tests/api_tests/test_autonomous_system.py` | **New** — comprehensive tests |

---

## Open Questions

1. **Protocol FK now or later?** We could ship ASN as a standalone resource first, then add the Protocol FK in a follow-up. Keeps the PR smaller and more focused.

2. **Natural key for URL:** Should `/api/autonomous_systems/65001/` work? This means `lookup_field = "number"` on the viewset. Device uses hostname as natural key, so there's precedent. The question is whether the number alone is unambiguous enough (it's unique per site, and the site is in the URL path).

3. **ASDOT display:** Include `number_asdot` as a read-only serializer field? It's only meaningful for 32-bit ASNs (≥65536), but it's a nice touch for operators who think in ASDOT notation.

4. **`PositiveIntegerField` vs `BigIntegerField`:** Django's `PositiveIntegerField` is a 32-bit unsigned int (max 2147483647 on most DBs), which is too small for the full 32-bit ASN range (max 4294967294). We likely need `PositiveBigIntegerField` or `BigIntegerField` with validators.

---

## References

- [dropbox/nsot#148](https://github.com/dropbox/nsot/issues/148) — Original feature request
- [RFC 6996](https://datatracker.ietf.org/doc/html/rfc6996) — Private ASN ranges
- [RFC 7300](https://datatracker.ietf.org/doc/html/rfc7300) — Last ASN reservation
- [RFC 7607](https://datatracker.ietf.org/doc/html/rfc7607) — AS0 processing
- [RFC 5396](https://datatracker.ietf.org/doc/html/rfc5396) — ASDOT notation
- [NetBox ASN model](https://github.com/netbox-community/netbox/blob/main/netbox/ipam/models/asns.py)
- [Nautobot BGP models](https://github.com/nautobot/nautobot-app-bgp-models/blob/develop/nautobot_bgp_models/models.py)
