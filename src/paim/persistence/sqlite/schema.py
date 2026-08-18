"""SQLAlchemy Core metadata for the generic Increment 1A schema."""

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
