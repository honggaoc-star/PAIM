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

# Increment 4 authoritative Integration, Boundary, Decision, and authorization families.
integration_records = Table(
    "integration_records",
    metadata,
    Column("integration_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

integration_versions = Table(
    "integration_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "integration_id",
        String(36),
        ForeignKey("integration_records.integration_id"),
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
    Column(
        "value_input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_acceptance_version_id",
        String(36),
        ForeignKey("input_acceptance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_acceptance_version_id",
        String(36),
        ForeignKey("input_acceptance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        nullable=False,
    ),
    Column("integrator_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('draft','ready','in_progress','completed','decision_pending',"
        "'superseded','withdrawn')",
        name="ck_integration_status",
    ),
    CheckConstraint(
        "(owner_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_integration_accountability",
    ),
)
Index(
    "ix_integration_context_time",
    integration_versions.c.case_id,
    integration_versions.c.configuration_version_id,
    integration_versions.c.use_context,
    integration_versions.c.purpose,
)

integration_material_applicability = Table(
    "integration_material_applicability",
    metadata,
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "applicability_version_id",
        String(36),
        ForeignKey("evidence_applicability_versions.version_id"),
        primary_key=True,
    ),
)
integration_authority_records = Table(
    "integration_authority_records",
    metadata,
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "authority_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        primary_key=True,
    ),
)
integration_authority_gaps = Table(
    "integration_authority_gaps",
    metadata,
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        primary_key=True,
    ),
)

uncertainty_classification_records = Table(
    "uncertainty_classification_records",
    metadata,
    Column("classification_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
uncertainty_classification_versions = Table(
    "uncertainty_classification_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "classification_id",
        String(36),
        ForeignKey("uncertainty_classification_records.classification_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        nullable=False,
    ),
    Column("proposed_decision_context", Text, nullable=False),
    Column("proposed_operating_state", Text, nullable=False),
    Column("source_reference", Text, nullable=False),
    Column(
        "source_input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=True,
    ),
    Column(
        "source_evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        nullable=True,
    ),
    Column("classification", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "classification IN ('ACCEPTED_UNCERTAINTY','DECISION_LIMITING_UNCERTAINTY')",
        name="ck_uncertainty_classification",
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_uncertainty_accountability",
    ),
)
Index(
    "ix_uncertainty_decision_context",
    uncertainty_classification_versions.c.integration_version_id,
    uncertainty_classification_versions.c.proposed_decision_context,
    uncertainty_classification_versions.c.proposed_operating_state,
)

boundary_snapshot_records = Table(
    "boundary_snapshot_records",
    metadata,
    Column("snapshot_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
boundary_snapshot_versions = Table(
    "boundary_snapshot_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "snapshot_id",
        String(36),
        ForeignKey("boundary_snapshot_records.snapshot_id"),
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
    Column(
        "integration_id",
        String(36),
        ForeignKey("integration_records.integration_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        nullable=False,
    ),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('draft','finalized','superseded','withdrawn')",
        name="ck_boundary_snapshot_status",
    ),
)
Index(
    "ix_boundary_context",
    boundary_snapshot_versions.c.case_id,
    boundary_snapshot_versions.c.configuration_version_id,
    boundary_snapshot_versions.c.integration_version_id,
)

boundary_clause_records = Table(
    "boundary_clause_records",
    metadata,
    Column("clause_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
boundary_clause_versions = Table(
    "boundary_clause_versions",
    metadata,
    Column(
        "clause_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column(
        "clause_id", String(36), ForeignKey("boundary_clause_records.clause_id"), nullable=False
    ),
    Column(
        "snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column("clause_type", Text, nullable=False),
    Column("effect", Text, nullable=False),
    Column("target_reference", Text, nullable=True),
    Column("structured_reference", Text, nullable=True),
    Column("operator", Text, nullable=True),
    Column("structured_value", Text, nullable=True),
    Column("unit", Text, nullable=True),
    Column("narrative", Text, nullable=False),
    Column("verification_mode", Text, nullable=False),
    CheckConstraint(
        "effect IN ('permitted','excluded','required','limited','conditional','indeterminate')",
        name="ck_boundary_clause_effect",
    ),
    CheckConstraint(
        "verification_mode IN ('mechanically_testable','human_determination_required',"
        "'external_determination_required','indeterminate')",
        name="ck_boundary_clause_verification",
    ),
    CheckConstraint(
        "verification_mode <> 'mechanically_testable' OR "
        "(operator IS NOT NULL AND structured_value IS NOT NULL)",
        name="ck_boundary_mechanical_structure",
    ),
)
Index(
    "ix_boundary_clause_snapshot",
    boundary_clause_versions.c.snapshot_version_id,
    boundary_clause_versions.c.clause_type,
    boundary_clause_versions.c.target_reference,
)

boundary_determination_records = Table(
    "boundary_determination_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
boundary_determination_versions = Table(
    "boundary_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("boundary_determination_records.determination_id"),
        nullable=False,
    ),
    Column(
        "snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "clause_id", String(36), ForeignKey("boundary_clause_records.clause_id"), nullable=False
    ),
    Column(
        "clause_version_id",
        String(36),
        ForeignKey("boundary_clause_versions.clause_version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "outcome IN ('PASS','BREACH','INDETERMINATE')", name="ck_boundary_determination_outcome"
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_boundary_determination_accountability",
    ),
)
Index(
    "ix_boundary_determination_context",
    boundary_determination_versions.c.snapshot_version_id,
    boundary_determination_versions.c.clause_version_id,
)
boundary_determination_evidence = Table(
    "boundary_determination_evidence",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("boundary_determination_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
)

decision_records = Table(
    "decision_records",
    metadata,
    Column("decision_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
decision_versions = Table(
    "decision_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("decision_id", String(36), ForeignKey("decision_records.decision_id"), nullable=False),
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
    Column(
        "integration_id",
        String(36),
        ForeignKey("integration_records.integration_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_id",
        String(36),
        ForeignKey("boundary_snapshot_records.snapshot_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column("proposed_action", Text, nullable=False),
    Column("operating_state", Text, nullable=False),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('proposed','pending_authorization','authorized','superseded',"
        "'withdrawn','expired')",
        name="ck_decision_status",
    ),
)
Index(
    "ix_decision_current_context",
    decision_versions.c.case_id,
    decision_versions.c.configuration_version_id,
)

decision_uncertainty_links = Table(
    "decision_uncertainty_links",
    metadata,
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "classification_version_id",
        String(36),
        ForeignKey("uncertainty_classification_versions.version_id"),
        primary_key=True,
    ),
    Column("classification", Text, nullable=False),
)
decision_authority_records = Table(
    "decision_authority_records",
    metadata,
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "authority_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        primary_key=True,
    ),
)
decision_authority_gaps = Table(
    "decision_authority_gaps",
    metadata,
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        primary_key=True,
    ),
)

bounded_proceed_records = Table(
    "bounded_proceed_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
bounded_proceed_versions = Table(
    "bounded_proceed_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("bounded_proceed_records.determination_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "unresolved_gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        nullable=False,
    ),
    Column("blocked_broader_decision", Text, nullable=False),
    Column("narrower_scope", Text, nullable=False),
    Column("operating_state", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "authority_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("authority_mechanism", Text, nullable=True),
    Column(
        "authority_record_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "(authority_assignment_version_id IS NOT NULL AND authority_mechanism IS NULL) OR "
        "(authority_assignment_version_id IS NULL AND authority_mechanism IS NOT NULL)",
        name="ck_bounded_proceed_authority",
    ),
    CheckConstraint(
        "authority_record_version_id IS NOT NULL OR authority_mechanism IS NOT NULL",
        name="ck_bounded_proceed_authority_source",
    ),
)
bounded_proceed_delegations = Table(
    "bounded_proceed_delegations",
    metadata,
    Column(
        "bounded_proceed_version_id",
        String(36),
        ForeignKey("bounded_proceed_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)
bounded_proceed_boundary_clauses = Table(
    "bounded_proceed_boundary_clauses",
    metadata,
    Column(
        "bounded_proceed_version_id",
        String(36),
        ForeignKey("bounded_proceed_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "clause_version_id",
        String(36),
        ForeignKey("boundary_clause_versions.clause_version_id"),
        primary_key=True,
    ),
)

decision_authorization_basis_records = Table(
    "decision_authorization_basis_records",
    metadata,
    Column("basis_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
decision_authorization_basis_versions = Table(
    "decision_authorization_basis_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "basis_id",
        String(36),
        ForeignKey("decision_authorization_basis_records.basis_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column("decision_authority_identity", Text, nullable=False),
    Column(
        "authority_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("authority_mechanism", Text, nullable=True),
    Column(
        "authority_record_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        nullable=True,
    ),
    Column("authorized_scope", Text, nullable=False),
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
    Column("operating_state_coverage_json", Text, nullable=False),
    Column("decision_type", Text, nullable=False),
    Column("organizational_unit", Text, nullable=True),
    Column("authorization_event_id", String(36), nullable=False, unique=True),
    Column(
        "authorization_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False
    ),
    Column("authorization_effective_at_us", BigInteger, nullable=False),
    Column(
        "bounded_proceed_version_id",
        String(36),
        ForeignKey("bounded_proceed_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "(authority_assignment_version_id IS NOT NULL AND authority_mechanism IS NULL) OR "
        "(authority_assignment_version_id IS NULL AND authority_mechanism IS NOT NULL)",
        name="ck_decision_authorization_authority",
    ),
    CheckConstraint(
        "authority_record_version_id IS NOT NULL OR authority_mechanism IS NOT NULL",
        name="ck_decision_authorization_source",
    ),
)
Index(
    "ix_authorization_decision",
    decision_authorization_basis_versions.c.decision_version_id,
    decision_authorization_basis_versions.c.authorization_effective_at_us,
)
decision_authorization_delegations = Table(
    "decision_authorization_delegations",
    metadata,
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)
decision_authorization_gaps = Table(
    "decision_authorization_gaps",
    metadata,
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        primary_key=True,
    ),
)

# Increment 5 authoritative Intervention, activation, and Learning families.
decision_preauthorized_activation_mechanisms = Table(
    "decision_preauthorized_activation_mechanisms",
    metadata,
    Column("mechanism_version_id", String(36), primary_key=True),
    Column("mechanism_id", String(36), nullable=False),
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("rule_version", Text, nullable=False),
    Column("scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
    Column("limits_json", Text, nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    Column("effective_to_us", BigInteger, nullable=True),
    CheckConstraint(
        "effective_to_us IS NULL OR effective_to_us > effective_from_us",
        name="ck_activation_mechanism_effective",
    ),
)
Index(
    "ix_activation_mechanism_basis",
    decision_preauthorized_activation_mechanisms.c.basis_version_id,
    decision_preauthorized_activation_mechanisms.c.mechanism_id,
)

intervention_records = Table(
    "intervention_records",
    metadata,
    Column("intervention_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
intervention_versions = Table(
    "intervention_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
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
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('PROPOSED','PLANNED','IN_PROGRESS','BLOCKED','PARTIALLY_COMPLETED',"
        "'COMPLETED','FAILED','CANCELLED','SUPERSEDED')",
        name="ck_intervention_status",
    ),
    CheckConstraint(
        "(owner_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_intervention_accountability",
    ),
)
Index(
    "ix_intervention_context",
    intervention_versions.c.case_id,
    intervention_versions.c.decision_version_id,
    intervention_versions.c.configuration_version_id,
)

obligation_set_records = Table(
    "obligation_set_records",
    metadata,
    Column("obligation_set_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
obligation_set_versions = Table(
    "obligation_set_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "obligation_set_id",
        String(36),
        ForeignKey("obligation_set_records.obligation_set_id"),
        nullable=False,
    ),
    Column("decision_id", String(36), ForeignKey("decision_records.decision_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
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
)
Index(
    "ix_obligation_set_context_time",
    obligation_set_versions.c.decision_version_id,
    obligation_set_versions.c.configuration_version_id,
)

obligation_records = Table(
    "obligation_records",
    metadata,
    Column("obligation_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
obligation_versions = Table(
    "obligation_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "obligation_id",
        String(36),
        ForeignKey("obligation_records.obligation_id"),
        nullable=False,
    ),
    Column(
        "obligation_set_version_id",
        String(36),
        ForeignKey("obligation_set_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column("requirement_type", Text, nullable=False),
    Column("post_operation_permitted", Boolean, nullable=False),
    Column("post_operation_timing_conditions_json", Text, nullable=False),
    CheckConstraint(
        "requirement_type IN ('REQUIRED_BEFORE_OPERATION','REQUIRED_AFTER_OPERATION','OPTIONAL')",
        name="ck_obligation_requirement_type",
    ),
)
Index(
    "ix_obligation_set_type",
    obligation_versions.c.obligation_set_version_id,
    obligation_versions.c.requirement_type,
)

completion_result_records = Table(
    "completion_result_records",
    metadata,
    Column("result_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
completion_result_versions = Table(
    "completion_result_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "result_id",
        String(36),
        ForeignKey("completion_result_records.result_id"),
        nullable=False,
    ),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("performer_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
)
Index(
    "ix_completion_result_obligation",
    completion_result_versions.c.obligation_version_id,
)
completion_result_criteria = Table(
    "completion_result_criteria",
    metadata,
    Column(
        "result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column("criterion", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    CheckConstraint(
        "outcome IN ('MET','NOT_MET','INDETERMINATE')", name="ck_completion_criterion_outcome"
    ),
)
completion_result_evidence = Table(
    "completion_result_evidence",
    metadata,
    Column(
        "result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
)

completion_acceptor_mechanism_records = Table(
    "completion_acceptor_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
completion_acceptor_mechanism_versions = Table(
    "completion_acceptor_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("completion_acceptor_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
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
    Column(
        "accountable_actor_id",
        String(36),
        ForeignKey("paim_actors.actor_id"),
        nullable=False,
    ),
    Column("rule_version", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
)
Index(
    "ix_completion_acceptor_mechanism_context",
    completion_acceptor_mechanism_versions.c.intervention_id,
    completion_acceptor_mechanism_versions.c.decision_version_id,
    completion_acceptor_mechanism_versions.c.configuration_id,
    completion_acceptor_mechanism_versions.c.case_id,
)

completion_acceptance_records = Table(
    "completion_acceptance_records",
    metadata,
    Column("acceptance_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
completion_acceptance_versions = Table(
    "completion_acceptance_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "acceptance_id",
        String(36),
        ForeignKey("completion_acceptance_records.acceptance_id"),
        nullable=False,
    ),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "completion_result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "accountable_mechanism_version_id",
        String(36),
        ForeignKey("completion_acceptor_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint("outcome IN ('ACCEPTED','REJECTED')", name="ck_completion_acceptance_outcome"),
    CheckConstraint(
        "status IN ('CURRENT','WITHDRAWN','SUPERSEDED')",
        name="ck_completion_acceptance_status",
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND "
        "accountable_mechanism_version_id IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND "
        "accountable_mechanism_version_id IS NOT NULL)",
        name="ck_completion_acceptance_accountability",
    ),
)
Index(
    "ix_completion_acceptance_obligation",
    completion_acceptance_versions.c.obligation_version_id,
)
completion_acceptance_delegations = Table(
    "completion_acceptance_delegations",
    metadata,
    Column(
        "acceptance_version_id",
        String(36),
        ForeignKey("completion_acceptance_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

intervention_replacement_records = Table(
    "intervention_replacement_records",
    metadata,
    Column("replacement_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
intervention_replacement_versions = Table(
    "intervention_replacement_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "replacement_id",
        String(36),
        ForeignKey("intervention_replacement_records.replacement_id"),
        nullable=False,
    ),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "predecessor_intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "replacement_intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column("substantive_change", Boolean, nullable=False),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "predecessor_intervention_version_id <> replacement_intervention_version_id",
        name="ck_replacement_distinct_interventions",
    ),
)
Index(
    "ix_replacement_obligation",
    intervention_replacement_versions.c.obligation_version_id,
)

continued_validity_mechanism_records = Table(
    "continued_validity_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
continued_validity_mechanism_versions = Table(
    "continued_validity_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("continued_validity_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column(
        "successor_obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
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
    Column(
        "accountable_actor_id",
        String(36),
        ForeignKey("paim_actors.actor_id"),
        nullable=False,
    ),
    Column("rule_version", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
)
Index(
    "ix_continued_validity_mechanism_context",
    continued_validity_mechanism_versions.c.successor_obligation_version_id,
    continued_validity_mechanism_versions.c.decision_version_id,
    continued_validity_mechanism_versions.c.configuration_version_id,
)

continued_validity_records = Table(
    "continued_validity_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
continued_validity_versions = Table(
    "continued_validity_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("continued_validity_records.determination_id"),
        nullable=False,
    ),
    Column(
        "successor_obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_completion_result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_acceptance_version_id",
        String(36),
        ForeignKey("completion_acceptance_versions.version_id"),
        nullable=False,
    ),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "accountable_mechanism_version_id",
        String(36),
        ForeignKey("continued_validity_mechanism_versions.version_id"),
        nullable=True,
    ),
    Column("all_coverage_established", Boolean, nullable=False),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND "
        "accountable_mechanism_version_id IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND "
        "accountable_mechanism_version_id IS NOT NULL)",
        name="ck_continued_validity_accountability",
    ),
)
Index(
    "ix_continued_validity_obligation",
    continued_validity_versions.c.successor_obligation_version_id,
)
continued_validity_delegations = Table(
    "continued_validity_delegations",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("continued_validity_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

prerequisite_evaluation_basis_records = Table(
    "prerequisite_evaluation_basis_records",
    metadata,
    Column("basis_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
prerequisite_evaluation_basis_versions = Table(
    "prerequisite_evaluation_basis_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "basis_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_records.basis_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "obligation_set_version_id",
        String(36),
        ForeignKey("obligation_set_versions.version_id"),
        nullable=False,
    ),
    Column("aggregate_result", Text, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint(
        "aggregate_result IN ('SATISFIED','NOT_REQUIRED','NOT_ESTABLISHED','INCOMPLETE',"
        "'BLOCKED','CONFLICT')",
        name="ck_prerequisite_basis_result",
    ),
)
prerequisite_evaluation_basis_items = Table(
    "prerequisite_evaluation_basis_items",
    metadata,
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=True,
    ),
    Column(
        "completion_result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        nullable=True,
    ),
    Column(
        "completion_acceptance_version_id",
        String(36),
        ForeignKey("completion_acceptance_versions.version_id"),
        nullable=True,
    ),
    Column(
        "replacement_version_id",
        String(36),
        ForeignKey("intervention_replacement_versions.version_id"),
        nullable=True,
    ),
    Column(
        "reuse_determination_version_id",
        String(36),
        ForeignKey("continued_validity_versions.version_id"),
        nullable=True,
    ),
    Column("result", Text, nullable=False),
    Column("diagnostics_json", Text, nullable=False),
    CheckConstraint(
        "result IN ('SATISFIED','NOT_ESTABLISHED','INCOMPLETE','BLOCKED','CONFLICT')",
        name="ck_prerequisite_item_result",
    ),
)

activation_authorization_records = Table(
    "activation_authorization_records",
    metadata,
    Column("authorization_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
activation_authorization_versions = Table(
    "activation_authorization_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "authorization_id",
        String(36),
        ForeignKey("activation_authorization_records.authorization_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("operating_state", Text, nullable=False),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prerequisite_basis_version_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_versions.version_id"),
        nullable=False,
    ),
    Column("authority_kind", Text, nullable=False),
    Column("authority_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=True),
    Column(
        "authority_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("decision_preauthorized_activation_mechanisms.mechanism_version_id"),
        nullable=True,
    ),
    Column(
        "decision_authorization_basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("authority_scope", Text, nullable=False),
    Column("authority_limits_json", Text, nullable=False),
    Column("authority_effective_from_us", BigInteger, nullable=False),
    Column("authority_effective_to_us", BigInteger, nullable=True),
    Column("activation_effective_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "authority_kind IN ('DECISION_AUTHORITY','ORGANIZATIONAL_MECHANISM')",
        name="ck_activation_authority_kind",
    ),
    CheckConstraint(
        "(authority_kind = 'DECISION_AUTHORITY' AND authority_actor_id IS NOT NULL "
        "AND authority_assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(authority_kind = 'ORGANIZATIONAL_MECHANISM' AND authority_actor_id IS NULL "
        "AND authority_assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_activation_authority_path",
    ),
)
Index(
    "ix_activation_authorization_context",
    activation_authorization_versions.c.decision_version_id,
    activation_authorization_versions.c.configuration_version_id,
    activation_authorization_versions.c.activation_effective_at_us,
)
activation_authorization_delegations = Table(
    "activation_authorization_delegations",
    metadata,
    Column(
        "authorization_version_id",
        String(36),
        ForeignKey("activation_authorization_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

target_activation_events = Table(
    "target_activation_events",
    metadata,
    Column("event_id", String(36), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prerequisite_basis_version_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_versions.version_id"),
        nullable=False,
    ),
    Column(
        "activation_authorization_version_id",
        String(36),
        ForeignKey("activation_authorization_versions.version_id"),
        nullable=False,
    ),
    Column("operating_state", Text, nullable=False),
    Column("lifecycle_event_id", String(36), ForeignKey("status_events.event_id"), nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
)
Index(
    "ix_target_activation_history",
    target_activation_events.c.case_id,
    target_activation_events.c.effective_at_us,
    target_activation_events.c.recorded_at_us,
)

learning_item_records = Table(
    "learning_item_records",
    metadata,
    Column("learning_item_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
learning_item_versions = Table(
    "learning_item_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "learning_item_id",
        String(36),
        ForeignKey("learning_item_records.learning_item_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
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
    Column(
        "uncertainty_version_id",
        String(36),
        ForeignKey("uncertainty_classification_versions.version_id"),
        nullable=False,
    ),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "status IN ('PROPOSED','ACTIVE','AWAITING_EVIDENCE','COMPLETED','INCONCLUSIVE',"
        "'CANCELLED','SUPERSEDED')",
        name="ck_learning_item_status",
    ),
    CheckConstraint(
        "(owner_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_learning_item_accountability",
    ),
)
Index(
    "ix_learning_item_decision",
    learning_item_versions.c.case_id,
    learning_item_versions.c.decision_version_id,
)
learning_item_evidence = Table(
    "learning_item_evidence",
    metadata,
    Column(
        "learning_item_version_id",
        String(36),
        ForeignKey("learning_item_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
)

# Increment 6 — Trigger, Reassessment, and restrictive Interim Disposition.
# Currentness and Trigger Coverage are intentionally derived from immutable facts.
reassessment_mechanism_records = Table(
    "reassessment_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
reassessment_mechanism_versions = Table(
    "reassessment_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("reassessment_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column("function", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("rule_version", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
    Column("limits_json", Text, nullable=False),
    CheckConstraint(
        "function IN ('Trigger Determiner','Reassessment Owner',"
        "'Reassessment Coordination Authority')",
        name="ck_reassessment_mechanism_function",
    ),
)
Index(
    "ix_reassessment_mechanism_context",
    reassessment_mechanism_versions.c.function,
    reassessment_mechanism_versions.c.case_id,
    reassessment_mechanism_versions.c.decision_version_id,
    reassessment_mechanism_versions.c.configuration_version_id,
)

trigger_records = Table(
    "trigger_records",
    metadata,
    Column("trigger_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
trigger_versions = Table(
    "trigger_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("trigger_id", String(36), ForeignKey("trigger_records.trigger_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("trigger_type", Text, nullable=False),
    Column("management_question", Text, nullable=False),
    Column("affected_scope_json", Text, nullable=False),
    Column("source_kind", Text, nullable=False),
    Column("source_family", Text, nullable=False),
    Column("source_record_id", Text, nullable=False),
    Column("source_version_id", Text, nullable=False),
    Column("source_system", Text, nullable=True),
    Column("source_actor", Text, nullable=True),
    Column("source_event_id", Text, nullable=False),
    Column("source_knowledge_at_us", BigInteger, nullable=False),
    Column("withdrawn", Boolean, nullable=False, default=False),
    CheckConstraint(
        "source_kind IN ('PAIM_RECORD','HUMAN_EXTERNAL')", name="ck_trigger_source_kind"
    ),
)
Index(
    "ix_trigger_case_source_question",
    trigger_versions.c.case_id,
    trigger_versions.c.source_event_id,
    trigger_versions.c.management_question,
)

trigger_determination_records = Table(
    "trigger_determination_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
trigger_determination_versions = Table(
    "trigger_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("trigger_determination_records.determination_id"),
        nullable=False,
    ),
    Column(
        "trigger_version_id", String(36), ForeignKey("trigger_versions.version_id"), nullable=False
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("reassessment_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "outcome IN ('INFORMATIONAL','MONITOR','ANALYTICAL_REFRESH','REASSESSMENT_REQUIRED',"
        "'IMMEDIATE_DISPOSITION_AND_REASSESSMENT')",
        name="ck_trigger_determination_outcome",
    ),
    CheckConstraint(
        "(assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_trigger_determination_accountability",
    ),
)
Index("ix_trigger_determination_trigger", trigger_determination_versions.c.trigger_version_id)

reassessment_records = Table(
    "reassessment_records",
    metadata,
    Column("reassessment_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
reassessment_versions = Table(
    "reassessment_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "reassessment_id",
        String(36),
        ForeignKey("reassessment_records.reassessment_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("purpose", Text, nullable=False),
    Column("affected_scope_json", Text, nullable=False),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "owner_mechanism_version_id",
        String(36),
        ForeignKey("reassessment_mechanism_versions.version_id"),
        nullable=True,
    ),
    Column("initial_status", Text, nullable=False),
    CheckConstraint(
        "initial_status IN ('PROPOSED','OPEN','ANALYSIS_IN_PROGRESS','AWAITING_DECISION_AUTHORITY',"
        "'BLOCKED_CONFLICT','COMPLETED_CONFIRMED','COMPLETED_SUCCESSOR_DECISION','CANCELLED','SUPERSEDED')",
        name="ck_reassessment_status",
    ),
    CheckConstraint(
        "(initial_status = 'PROPOSED' AND owner_assignment_version_id IS NULL "
        "AND owner_mechanism_version_id IS NULL) OR "
        "(owner_assignment_version_id IS NOT NULL AND owner_mechanism_version_id IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND owner_mechanism_version_id IS NOT NULL)",
        name="ck_reassessment_owner_accountability",
    ),
)
Index(
    "ix_reassessment_case_context",
    reassessment_versions.c.case_id,
    reassessment_versions.c.decision_version_id,
    reassessment_versions.c.configuration_version_id,
)

trigger_membership_records = Table(
    "trigger_membership_records",
    metadata,
    Column("membership_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
trigger_membership_versions = Table(
    "trigger_membership_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "membership_id",
        String(36),
        ForeignKey("trigger_membership_records.membership_id"),
        nullable=False,
    ),
    Column(
        "trigger_version_id", String(36), ForeignKey("trigger_versions.version_id"), nullable=False
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=False,
    ),
    Column("membership_scope", Text, nullable=False),
    Column("active", Boolean, nullable=False),
    UniqueConstraint(
        "trigger_version_id",
        "reassessment_version_id",
        name="uq_trigger_reassessment_membership",
    ),
)
trigger_set_members = Table(
    "trigger_set_members",
    metadata,
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "trigger_version_id", String(36), ForeignKey("trigger_versions.version_id"), nullable=False
    ),
    Column(
        "membership_version_id",
        String(36),
        ForeignKey("trigger_membership_versions.version_id"),
        nullable=False,
    ),
    UniqueConstraint(
        "reassessment_version_id",
        "trigger_version_id",
        name="uq_trigger_set_trigger",
    ),
)

reassessment_determination_records = Table(
    "reassessment_determination_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
reassessment_determination_versions = Table(
    "reassessment_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("reassessment_determination_records.determination_id"),
        nullable=False,
    ),
    Column("kind", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column(
        "target_reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "canonical_trigger_version_id",
        String(36),
        ForeignKey("trigger_versions.version_id"),
        nullable=True,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("affected_scope_json", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("reassessment_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "kind IN ('GROUPING','DUPLICATE','COEXISTENCE','CANCELLATION','SUPERSESSION')",
        name="ck_reassessment_determination_kind",
    ),
    CheckConstraint(
        "outcome IN ('COMPATIBLE','INCOMPATIBLE','DUPLICATE','COEXISTENCE_AUTHORIZED',"
        "'CANCELLATION_AUTHORIZED','SUPERSESSION_AUTHORIZED')",
        name="ck_reassessment_determination_outcome",
    ),
    CheckConstraint(
        "(assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_reassessment_determination_accountability",
    ),
)
reassessment_determination_triggers = Table(
    "reassessment_determination_triggers",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("reassessment_determination_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "trigger_version_id",
        String(36),
        ForeignKey("trigger_versions.version_id"),
        primary_key=True,
    ),
)
reassessment_determination_reassessments = Table(
    "reassessment_determination_reassessments",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("reassessment_determination_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        primary_key=True,
    ),
)

interim_disposition_records = Table(
    "interim_disposition_records",
    metadata,
    Column("disposition_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
interim_disposition_versions = Table(
    "interim_disposition_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "disposition_id",
        String(36),
        ForeignKey("interim_disposition_records.disposition_id"),
        nullable=False,
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column("affected_scope_json", Text, nullable=False),
    Column("operating_state", Text, nullable=True),
    Column("allowed_actions_json", Text, nullable=False),
    Column("required_controls_json", Text, nullable=False),
    Column("prohibitions_json", Text, nullable=False),
    Column("conditions_json", Text, nullable=False),
    Column("suspend_scope", Boolean, nullable=False),
    Column(
        "authority_basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("authority_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("expiry_at_us", BigInteger, nullable=True),
)
Index(
    "ix_interim_disposition_context_time",
    interim_disposition_versions.c.case_id,
    interim_disposition_versions.c.decision_version_id,
    interim_disposition_versions.c.configuration_version_id,
    interim_disposition_versions.c.expiry_at_us,
)

decision_confirmation_records = Table(
    "decision_confirmation_records",
    metadata,
    Column("confirmation_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
decision_confirmation_versions = Table(
    "decision_confirmation_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "confirmation_id",
        String(36),
        ForeignKey("decision_confirmation_records.confirmation_id"),
        nullable=False,
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=False,
        unique=True,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("confirmer_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
)

reassessment_completion_outcomes = Table(
    "reassessment_completion_outcomes",
    metadata,
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        primary_key=True,
    ),
    Column("path", Text, nullable=False),
    Column(
        "confirmation_version_id",
        String(36),
        ForeignKey("decision_confirmation_versions.version_id"),
        nullable=True,
    ),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=True,
    ),
    Column("completed_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "(path = 'CONFIRMED' AND confirmation_version_id IS NOT NULL "
        "AND successor_decision_version_id IS NULL) OR "
        "(path = 'SUCCESSOR_DECISION' AND confirmation_version_id IS NULL "
        "AND successor_decision_version_id IS NOT NULL)",
        name="ck_reassessment_exactly_one_completion",
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
