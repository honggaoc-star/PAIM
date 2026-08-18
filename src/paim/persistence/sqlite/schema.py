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

evidence_records = Table(
    "evidence_records",
    metadata,
    Column("evidence_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

evidence_versions = Table(
    "evidence_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("evidence_id", String(36), ForeignKey("evidence_records.evidence_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=True,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("classification", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
    Column("observed_at_us", BigInteger, nullable=True),
    Column("attention", Text, nullable=False),
    CheckConstraint(
        "classification IN ('observed', 'supported_inference', "
        "'estimate', 'assumption', 'unknown')",
        name="ck_evidence_classification",
    ),
    CheckConstraint(
        "attention IN ('current', 'refresh_required', 'stale')",
        name="ck_evidence_attention",
    ),
)
Index(
    "ix_evidence_versions_context",
    evidence_versions.c.evidence_id,
    evidence_versions.c.configuration_version_id,
)

authority_records = Table(
    "authority_records",
    metadata,
    Column("authority_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

authority_record_versions = Table(
    "authority_record_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "authority_id", String(36), ForeignKey("authority_records.authority_id"), nullable=False
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=True,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("category", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("requirement", Text, nullable=False),
)
Index(
    "ix_authority_versions_context",
    authority_record_versions.c.authority_id,
    authority_record_versions.c.configuration_version_id,
)

authority_gaps = Table(
    "authority_gaps",
    metadata,
    Column("gap_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

authority_gap_versions = Table(
    "authority_gap_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("gap_id", String(36), ForeignKey("authority_gaps.gap_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("question_id", Text, nullable=False),
    Column("question", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
)
Index(
    "ix_authority_gaps_context",
    authority_gap_versions.c.case_id,
    authority_gap_versions.c.configuration_version_id,
)

exact_evidence_links = Table(
    "exact_evidence_links",
    metadata,
    Column(
        "source_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
    Column("link_role", Text, primary_key=True),
)

affected_use_references = Table(
    "affected_use_references",
    metadata,
    Column(
        "source_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column("use_reference", Text, primary_key=True),
)

evidence_applicability_records = Table(
    "evidence_applicability_records",
    metadata,
    Column("applicability_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

evidence_applicability_versions = Table(
    "evidence_applicability_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "applicability_id",
        String(36),
        ForeignKey("evidence_applicability_records.applicability_id"),
        nullable=False,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        nullable=False,
    ),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column(
        "target_version_id", String(36), ForeignKey("record_versions.version_id"), nullable=True
    ),
    Column("purpose", Text, nullable=False),
    Column("assessed_scope", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=True,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("outcome", Text, nullable=False),
    Column("conditions_json", Text, nullable=False),
    Column("limitations_json", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("assessor_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "target_type IN ('managed_configuration_version', 'value_input_version', "
        "'risk_input_version', 'authority_record_version', 'authority_gap')",
        name="ck_applicability_target_type",
    ),
    CheckConstraint(
        "outcome IN ('APPLICABLE', 'CONDITIONALLY_APPLICABLE', 'PARTIALLY_APPLICABLE', "
        "'NOT_APPLICABLE', 'INDETERMINATE')",
        name="ck_applicability_outcome",
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_applicability_accountability_exactly_one",
    ),
)
Index(
    "ix_applicability_exact_context",
    evidence_applicability_versions.c.evidence_version_id,
    evidence_applicability_versions.c.target_type,
    evidence_applicability_versions.c.target_id,
    evidence_applicability_versions.c.target_version_id,
    evidence_applicability_versions.c.purpose,
    evidence_applicability_versions.c.assessed_scope,
)

analytical_inputs = Table(
    "analytical_inputs",
    metadata,
    Column("input_id", String(36), ForeignKey("records.record_id"), primary_key=True),
    Column("lane", Text, nullable=False),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_analytical_input_lane"),
)

analytical_input_versions = Table(
    "analytical_input_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("input_id", String(36), ForeignKey("analytical_inputs.input_id"), nullable=False),
    Column("lane", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("purpose", Text, nullable=False),
    Column("finding", Text, nullable=False),
    Column("boundary", Text, nullable=False),
    Column("uncertainties_json", Text, nullable=False),
    Column("implication", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_analytical_input_version_lane"),
)
Index(
    "ix_analytical_inputs_selection_context",
    analytical_input_versions.c.lane,
    analytical_input_versions.c.configuration_version_id,
    analytical_input_versions.c.purpose,
)

candidate_dispositions = Table(
    "candidate_dispositions",
    metadata,
    Column("disposition_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

candidate_disposition_versions = Table(
    "candidate_disposition_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "disposition_id",
        String(36),
        ForeignKey("candidate_dispositions.disposition_id"),
        nullable=False,
    ),
    Column(
        "input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("disposition", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_candidate_disposition_lane"),
    CheckConstraint(
        "disposition IN ('NON_SELECTED', 'DISSENTING', 'REJECTED_FOR_USE', "
        "'WITHDRAWN', 'SUPERSEDED')",
        name="ck_candidate_disposition_outcome",
    ),
)
Index(
    "ix_candidate_disposition_context",
    candidate_disposition_versions.c.input_version_id,
    candidate_disposition_versions.c.use_context,
    candidate_disposition_versions.c.purpose,
)

lane_fitness_records = Table(
    "lane_fitness_records",
    metadata,
    Column("fitness_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

lane_fitness_versions = Table(
    "lane_fitness_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("fitness_id", String(36), ForeignKey("lane_fitness_records.fitness_id"), nullable=False),
    Column("lane", Text, nullable=False),
    Column(
        "input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("indeterminate_treatment", Text, nullable=True),
    Column("decision_limiting", Boolean, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_lane_fitness_lane"),
    CheckConstraint("outcome IN ('SUPPORTABLE', 'BLOCKED')", name="ck_lane_fitness_outcome"),
    CheckConstraint("length(trim(rationale)) > 0", name="ck_lane_fitness_rationale"),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_lane_fitness_accountability_exactly_one",
    ),
)
Index(
    "ix_lane_fitness_context",
    lane_fitness_versions.c.lane,
    lane_fitness_versions.c.configuration_version_id,
    lane_fitness_versions.c.use_context,
    lane_fitness_versions.c.purpose,
)

material_evidence_basis = Table(
    "material_evidence_basis",
    metadata,
    Column(
        "fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "applicability_version_id",
        String(36),
        ForeignKey("evidence_applicability_versions.version_id"),
        primary_key=True,
    ),
    Column("role", Text, nullable=False),
    Column("required_support", Boolean, nullable=False),
    Column("claimed_scope", Text, nullable=False),
)

input_acceptance_records = Table(
    "input_acceptance_records",
    metadata,
    Column("acceptance_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

input_acceptance_versions = Table(
    "input_acceptance_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "acceptance_id",
        String(36),
        ForeignKey("input_acceptance_records.acceptance_id"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column(
        "input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column(
        "fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        nullable=False,
    ),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_input_acceptance_lane"),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_input_acceptance_accountability_exactly_one",
    ),
)
Index(
    "ix_input_acceptance_selection_context",
    input_acceptance_versions.c.lane,
    input_acceptance_versions.c.configuration_version_id,
    input_acceptance_versions.c.use_context,
    input_acceptance_versions.c.purpose,
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
