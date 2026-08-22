# RWR Small-Business Lending Source Reconstruction

## Purpose and source boundary

This document reconstructs only what the current Return-Weighted Risk (RWR) paper says about its
small-business-lending illustration. It does not convert the illustration into a PAIM case and does not
claim that PAIM implements or validates RWR.

Authoritative source for this reconstruction:
[Return-Weighted Risk for Navigating an Evolving AI Landscape](https://github.com/honggaoc-star/AI-Risk-Management/blob/fab90200ff67c81cc793c463d58953a8192e921f/Return-Weighted-Risk/Return-Weighted-Risk-for-Navigating-an-Evolving-AI-Landscape.pdf),
AI-Risk-Management commit `fab90200ff67c81cc793c463d58953a8192e921f`, reviewed on
2026-08-22.

Page and section references below point to that PDF. The paper explicitly calls Aster Vale a
hypothetical illustration and says it is not evidence that the approach works across organizations or
uses (pp. 1, 15, Abstract and section 8.4).

## Classification convention

- **SOURCE** - directly stated by the RWR paper.
- **STRUCTURING INTERPRETATION** - a reasonable organization of source statements, not an
  additional source fact.
- **NOT ESTABLISHED** - information the paper does not supply.

No PAIM-created case fact appears in this reconstruction.

## Activity and people

| Element | Reconstruction | Classification and trace |
|---|---|---|
| Organization | Aster Vale Regional Bank, a hypothetical regional bank. | **SOURCE** - p. 2, section 1.1. |
| AI activity | A six-month restricted pilot of Navigator, a vendor-developed generative-AI system that organizes documents and drafts portions of credit memoranda for small-business loans. | **SOURCE** - p. 2, section 1.1. |
| Excluded AI actions | Navigator does not approve or decline applications, assign credit ratings, determine prices, or communicate directly with applicants. | **SOURCE** - p. 2, section 1.1. |
| Human role | Underwriters retain formal decision authority and certify every completed memorandum. | **SOURCE** - p. 2, section 1.1. |
| Governed activity | Navigator plus underwriters, source access, document types, verification practices, controls, and workflow are the relevant activity, rather than the model alone. | **SOURCE** - p. 4, section 2.2. |
| Pilot participants, portfolio size, loan thresholds, exact controls, decision committee, and vendor contract | Not specified. | **NOT ESTABLISHED**. |

## Original value case and alternatives

The original purpose was not merely faster credit-memorandum preparation. Aster Vale expected faster
preparation to contribute to faster decisions, lower applicant burden, and better access to
individualized review for smaller businesses. Those expectations formed the original value case
(p. 12, section 7.1).

The paper keeps multiple alternatives visible: retain the existing process, redesign workflow without
AI, use conventional automation, adopt a narrower AI-assisted tool, or continue with Navigator
(p. 12, section 7.1). It later reports that a non-AI workflow redesign achieved a similar end-to-end
improvement (pp. 2, 13, sections 1.1 and 7.2).

**STRUCTURING INTERPRETATION:** The source supports treating the initial value case as a causal
pathway - faster
preparation was expected to improve downstream outcomes - rather than treating preparation time as
value by itself. It does not provide an approved financial model, target benefit threshold, baseline
business case, or initial alternative comparison record.

## Independent risk case

The paper's general RWR model says the risk case asks what can go wrong, who may be affected, how
serious exposure may be, and whether controls make remaining risk acceptable. It must remain
independent of the value case; intended value may direct additional inquiry but cannot determine the
risk conclusion (p. 8, sections 4.4-4.5).

For Aster Vale, the paper reports risk-relevant pilot observations rather than a complete initial risk
assessment:

- no autonomous credit decision, serious privacy incident, or explicit breach of approved pilot risk
  limits was identified;
- standardized digital information performed better than scanned, handwritten, multilingual, or
  unconventional records;
- nonstandard-document processing time increased;
- some newer underwriters increasingly began with Navigator summaries;
- verification burden remained and source accessibility deteriorated;
- the bank became more dependent on a vendor it understood only partially.

These statements are **SOURCE** facts from pp. 2, 4, and 13 (sections 1.1, 2.4-2.5, and 7.2).

The paper does not state the initial risk taxonomy, independent assessor, residual-risk rating, exact
pilot limits, control tests, subgroup definitions, approval criteria, or initial risk-permissibility
conclusion. Those are **NOT ESTABLISHED**.

## Evidence timeline

### Before or at pilot authorization

The source implies that a restricted pilot had been authorized because it describes approved pilot risk
limits and a completed six-month pilot. It does not reconstruct the authorization event, its evidentiary
basis, its authority holder, or the original three-test conclusions.

That implication is a **STRUCTURING INTERPRETATION**, not a source record. The only direct source
statements are that the pilot existed, remained restricted, and had approved pilot risk limits (p. 2,
section 1.1).

### Evidence after the restricted pilot

| Dimension | Source observation | Source assessment | Trace |
|---|---|---|---|
| Financial | Preparation cost fell, but vendor, validation, quality-assurance, and integration costs absorbed much of the saving. | Directional | p. 13, Table 3. |
| Operational | Preparation time fell 28%; application-to-decision time fell 7%. | Mixed | pp. 2 and 13, section 1.1 and Table 3. |
| Customer | Repeated requests fell 4%; abandonment changed from 13.0% to 12.7%. | Insufficient | p. 13, Table 3. |
| Access | No attributable approval effect; weak improvement for standardized small applications. | Insufficient | p. 13, Table 3. |
| Distribution | Standard digital applications improved; nonstandard-document processing time rose 6%. | Uneven | p. 13, Table 3. |
| Workforce | Experienced users saved time; verification burden persisted; junior reliance increased. | Mixed | p. 13, Table 3. |
| Governance | Draft consistency improved; source accessibility fell from 94% to 64%. | Mixed / weakened | p. 13, Table 3. |
| Learning | Downstream bottlenecks, user differences, document limits, and scaling conditions became clearer. | Supported for pilot | p. 13, Table 3. |
| Comparative | Non-AI redesign reduced preparation time 17% and decision time 6%. | AI advantage limited | p. 13, Table 3. |

The paper says these labels are qualitative reading aids, not points on a common scale (pp. 12-13,
section 7.2 and Table 3). They must not be added, averaged, or ranked as a composite result.

## Revised request and material change

Management proposes expansion across all small-business-lending teams, larger loans, broader
document types, less quality-assurance coverage, and less-experienced underwriters. Its rationale shifts
from faster decisions, lower applicant burden, and improved access toward processing capacity, avoided
hiring, and strategic AI capability (pp. 2 and 13, sections 1.1 and 7.3).

The paper therefore presents simultaneous changes in:

- purpose and value rationale;
- user population and scale;
- document population;
- loan consequences;
- oversight conditions; and
- the relevance of pilot evidence to the proposed expansion.

It does not describe a vendor/model update, new threshold, new input feature, or completed mitigation
change. Those are **NOT ESTABLISHED**.

## RWR authorization reasoning

RWR describes three sequential tests (p. 9, section 5.1):

1. **Admissibility** - whether the action satisfies applicable legal, ethical, policy, and
   non-compensable constraints.
2. **Risk permissibility** - whether independently assessed residual risk is within authorized limits
   for the proposed scope and conditions.
3. **Value justification** - whether the current value case justifies undertaking that permissible
   residual risk.

Passing risk permissibility makes an action eligible for value judgment; it does not itself mean
approval. Value justification is governed judgment on explicit evidence, alternatives, costs, affected
parties, and uncertainty, not a universal score (p. 9, sections 5.1-5.2).

Applied to Aster Vale, the paper states:

- nothing suggests the restricted preparation use has become inadmissible;
- the pilot does not establish that residual risk is permissible for the proposed expansion;
- the original customer/access rationale has limited support;
- the revised efficiency rationale has not been tested against total implementation/control costs or
  the non-AI workflow alternative; and
- another controlled stage, rather than full expansion, is supported by the RWR analysis.

These are **SOURCE** statements from p. 14, section 7.4. The paper does not claim a uniquely correct
answer. It suggests restoring source access, retaining scope limits, comparing Navigator with workflow
redesign, examining workforce and distribution effects, and specifying evidence for broader use.

## Initial and continuing authorization

| Decision point | What the source establishes | What remains unknown |
|---|---|---|
| Initial pilot | A restricted six-month pilot occurred under approved pilot risk limits. | Exact action, authority, evidence package, admissibility result, risk-permissibility result, value-justification result, Boundary, and conditions. |
| Continue restricted use | The paper says nothing indicates the restricted preparation use has become inadmissible. | Whether Aster Vale actually reauthorized continuation and on what exact terms. |
| Proposed broad expansion | RWR analysis does not support full expansion on the available illustration; it supports another controlled stage. | Any real organizational vote, authorization record, implementation, or later result. |

The distinction between the paper's analytical disposition and an actual organizational authorization is
important: no actual post-pilot Decision is reported.

## Explicit future investigations

The paper says RWR has not been tested in live organizational decisions and may improve reasoning or
merely add governance effort. It proposes questions about risk discovery, decision effects, persistence
and burden, institutional design, and learning versus delay (pp. 15-16, section 8.4).

It suggests an initial comparative practitioner exercise: assess the same AI-use case under ordinary
governance and then under the RWR three-test approach; compare requested evidence, identified
dependencies, rationale, and disposition. The paper explicitly says this would not show improved
real-world outcomes, only whether decision-relevant reasoning changed (p. 16, section 8.4).

## Source gaps carried forward, not filled

The following must be supplied only as labeled PAIM-created scenario material if later exercises need
them:

- exact pilot-start date and decision record;
- organizational units, role holders, and authority assignments;
- governing policies or legal requirements;
- applicant segments and sample sizes;
- baseline costs and benefit thresholds;
- exact model, prompt, retrieval, data, or workflow Configuration;
- risk limits, controls, testing methods, and breach thresholds;
- causal attribution methods;
- later mitigation, alternative, or post-pilot outcomes; and
- the bank's actual final Decision.
