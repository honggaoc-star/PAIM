"""SQLAlchemy Core metadata for the PAIM integrity and Increment 2 schema."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

records = Table(
    "records",
    metadata,
    Column("record_id", String(36), primary_key=True),
    Column("family", Text, nullable=False),
    Column("scope", Text, nullable=False),
    UniqueConstraint("record_id", "family", "scope", name="uq_record_identity_scope"),
)

record_versions = Table(
    "record_versions",
    metadata,
    Column("version_id", String(36), primary_key=True),
    Column("record_id", String(36), ForeignKey("records.record_id"), nullable=False),
    Column("content_json", Text, nullable=False),
    Column("finalized", Boolean, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    Column("effective_to_us", BigInteger, nullable=True),
    Column("creator", Text, nullable=False),
    CheckConstraint(
        "effective_to_us IS NULL OR effective_to_us > effective_from_us",
        name="ck_version_effective_interval",
    ),
)
Index(
    "ix_versions_scope_time",
    record_versions.c.record_id,
    record_versions.c.effective_from_us,
    record_versions.c.effective_to_us,
    record_versions.c.recorded_at_us,
)

status_events = Table(
    "status_events",
    metadata,
    Column("event_id", String(36), primary_key=True),
    Column(
        "target_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("prior_status", Text, nullable=False),
    Column("new_status", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("actor", Text, nullable=False),
    Column("basis", Text, nullable=False),
)
Index(
    "ix_status_target_time",
    status_events.c.target_version_id,
    status_events.c.effective_at_us,
    status_events.c.recorded_at_us,
)

version_relationships = Table(
    "version_relationships",
    metadata,
    Column("relationship_id", String(36), primary_key=True),
    Column(
        "source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "target_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("relationship_type", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("reason", Text, nullable=False),
    CheckConstraint(
        "source_version_id <> target_version_id", name="ck_relationship_distinct_versions"
    ),
)
Index(
    "ix_relationship_source_target",
    version_relationships.c.source_version_id,
    version_relationships.c.target_version_id,
)

idempotency_facts = Table(
    "idempotency_facts",
    metadata,
    Column("scope", Text, primary_key=True),
    Column("idempotency_key", Text, primary_key=True),
    Column("digest", String(64), nullable=False),
    Column("command_id", String(36), nullable=False),
    Column("outcome_json", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
)

audit_facts = Table(
    "audit_facts",
    metadata,
    Column("audit_id", String(36), primary_key=True),
    Column("principal_id", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("actor_resolution", Text, nullable=False),
    Column("operation", Text, nullable=False),
    Column("result", Text, nullable=False),
    Column("command_id", String(36), nullable=False),
    Column("idempotency_scope", Text, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("correlation_id", Text, nullable=True),
    Column("causation_id", Text, nullable=True),
    Column("target_record_id", String(36), ForeignKey("records.record_id"), nullable=False),
    Column("affected_version_ids_json", Text, nullable=False),
    Column("expected_precondition", Text, nullable=False),
    Column("observed_precondition", Text, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("reason_outcomes_json", Text, nullable=False),
    Column("request_digest", String(64), nullable=False),
    CheckConstraint(
        "(actor_resolution = 'provided' AND actor_id IS NOT NULL) OR "
        "(actor_resolution IN ('unresolved', 'not_applicable') AND actor_id IS NULL)",
        name="ck_audit_actor_resolution",
    ),
)

paim_cases = Table(
    "paim_cases",
    metadata,
    Column("case_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

paim_case_versions = Table(
    "paim_case_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("initial_lifecycle_state", Text, nullable=False),
    CheckConstraint("initial_lifecycle_state = 'open'", name="ck_case_initial_state_open"),
)
Index("ix_case_versions_case", paim_case_versions.c.case_id)

paim_case_links = Table(
    "paim_case_links",
    metadata,
    Column("link_id", String(36), primary_key=True),
    Column("source_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("target_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("relationship_type", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("actor_id", String(36), nullable=False),
    Column("reason", Text, nullable=False),
    CheckConstraint("source_case_id <> target_case_id", name="ck_case_link_distinct_cases"),
)
Index(
    "ix_case_links_cases_time",
    paim_case_links.c.source_case_id,
    paim_case_links.c.target_case_id,
    paim_case_links.c.effective_at_us,
)

managed_configurations = Table(
    "managed_configurations",
    metadata,
    Column("configuration_id", String(36), ForeignKey("records.record_id"), primary_key=True),
    Column("owning_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
)
Index("ix_configurations_owning_case", managed_configurations.c.owning_case_id)

managed_configuration_versions = Table(
    "managed_configuration_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column("maturity", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    CheckConstraint("maturity IN ('draft', 'finalized')", name="ck_configuration_maturity"),
    CheckConstraint(
        "purpose IN ('candidate', 'proposed', 'experimental', 'alternative', 'fallback')",
        name="ck_configuration_purpose",
    ),
)
Index("ix_configuration_versions_identity", managed_configuration_versions.c.configuration_id)

paim_actors = Table(
    "paim_actors",
    metadata,
    Column("actor_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

paim_actor_versions = Table(
    "paim_actor_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
)
Index("ix_actor_versions_identity", paim_actor_versions.c.actor_id)

role_assignments = Table(
    "role_assignments",
    metadata,
    Column("assignment_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

role_assignment_versions = Table(
    "role_assignment_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "assignment_id",
        String(36),
        ForeignKey("role_assignments.assignment_id"),
        nullable=False,
    ),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("role", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("case_context_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column("accountable", Boolean, nullable=False),
    Column("compatibility_key", Text, nullable=False),
    Column("delegation_effect", Text, nullable=False),
    Column(
        "delegated_from_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "target_type IN ('organization', 'business_unit', 'case', 'configuration', "
        "'decision', 'intervention', 'authority_domain')",
        name="ck_role_target_type",
    ),
    CheckConstraint(
        "(target_type IN ('organization', 'business_unit') AND case_context_id IS NULL) OR "
        "(target_type = 'case' AND case_context_id = target_id) OR "
        "(target_type = 'configuration' AND case_context_id IS NOT NULL) OR "
        "(target_type IN ('decision', 'intervention', 'authority_domain'))",
        name="ck_role_case_context",
    ),
    CheckConstraint(
        "delegation_effect IN ('none', 'supplement', 'transfer', 'retain')",
        name="ck_role_delegation_effect",
    ),
    CheckConstraint(
        "(delegation_effect = 'none' AND delegated_from_version_id IS NULL) OR "
        "(delegation_effect <> 'none' AND delegated_from_version_id IS NOT NULL)",
        name="ck_role_delegation_source",
    ),
)
Index(
    "ix_role_assignments_resolution",
    role_assignment_versions.c.role,
    role_assignment_versions.c.target_type,
    role_assignment_versions.c.target_id,
    role_assignment_versions.c.case_context_id,
)

governing_configuration_designations = Table(
    "governing_configuration_designations",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_governing_accountability_exactly_one",
    ),
)
Index("ix_governing_designation_case", governing_configuration_designations.c.case_id)

configuration_determinations = Table(
    "configuration_determinations",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("determination_kind", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "determination_kind IN ('materiality', 'identity_continuity')",
        name="ck_determination_kind",
    ),
    CheckConstraint(
        "(determination_kind = 'materiality' AND outcome IN ('material', 'non_material')) OR "
        "(determination_kind = 'identity_continuity' AND "
        "outcome IN ('same_identity', 'new_identity'))",
        name="ck_determination_outcome",
    ),
    CheckConstraint("length(trim(rationale)) > 0", name="ck_determination_rationale"),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_determination_accountability_exactly_one",
    ),
)
Index(
    "ix_determination_configuration_kind",
    configuration_determinations.c.configuration_version_id,
    configuration_determinations.c.determination_kind,
)

IMMUTABILITY_TRIGGERS: tuple[str, ...] = (
    """
    CREATE TRIGGER prevent_finalized_version_update
    BEFORE UPDATE ON record_versions
    WHEN OLD.finalized = 1
    BEGIN
      SELECT RAISE(ABORT, 'finalized content is immutable');
    END
    """,
    """
    CREATE TRIGGER prevent_record_version_delete
    BEFORE DELETE ON record_versions
    BEGIN
      SELECT RAISE(ABORT, 'record version history is append-preserving');
    END
    """,
    """
    CREATE TRIGGER prevent_status_event_update
    BEFORE UPDATE ON status_events
    BEGIN
      SELECT RAISE(ABORT, 'status event history is append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_status_event_delete
    BEFORE DELETE ON status_events
    BEGIN
      SELECT RAISE(ABORT, 'status event history is append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_relationship_update
    BEFORE UPDATE ON version_relationships
    BEGIN
      SELECT RAISE(ABORT, 'version relationships are append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_relationship_delete
    BEFORE DELETE ON version_relationships
    BEGIN
      SELECT RAISE(ABORT, 'version relationships are append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_idempotency_update
    BEFORE UPDATE ON idempotency_facts
    BEGIN
      SELECT RAISE(ABORT, 'idempotency facts are immutable');
    END
    """,
    """
    CREATE TRIGGER prevent_idempotency_delete
    BEFORE DELETE ON idempotency_facts
    BEGIN
      SELECT RAISE(ABORT, 'idempotency facts are immutable');
    END
    """,
    """
    CREATE TRIGGER prevent_audit_update
    BEFORE UPDATE ON audit_facts
    BEGIN
      SELECT RAISE(ABORT, 'audit facts are append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_audit_delete
    BEFORE DELETE ON audit_facts
    BEGIN
      SELECT RAISE(ABORT, 'audit facts are append-only');
    END
    """,
)
