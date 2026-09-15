# A startup decision for a three-person technical team

## Executive verdict

**Choose lead handoff reconciliation for HubSpot automation agencies as the first problem to validate. Do not commit to building a general AI reliability platform.** The proposed product independently compares incoming lead submissions with the records and required fields that should exist in HubSpot, then gives the agency an evidence-backed list of missing, duplicated or incorrectly routed items.

This is a narrower combination of exception management and data reconciliation. Its usefulness does not depend on whether an AI agent or an ordinary workflow moved the data. The customer buys a trustworthy account of unfinished work and less manual checking; an AI explanation is optional.

The recommendation is **GO for a 30-day customer validation effort; NO-GO for an unconditional 12-month product commitment**. There is evidence that failures occur and that organizations assign people to operate automations. There is not yet evidence that enough agencies will buy this particular extra product. Public competitor prices demonstrate available offers, not sales, retention or willingness to pay for a new entrant.

Research cutoff is September 13, 2026. The assumed team is three technical founders with limited capital and no established enterprise distribution. Specific accounting expertise, existing customer relationships, available founder hours and budget were not established. These assumptions materially affect the choice.

### First choice: lead handoff reconciliation

**Customer and buyer.** An automation or RevOps agency managing several client HubSpot portals, already responsible for maintaining custom lead workflows. The owner or automation lead buys from the tooling or client-maintenance budget. Initially qualify agencies with at least five active client relationships and enough recurring checking or incident work to justify a subscription; these are proposed filters, not measured market averages.

**Pain.** A job ran, but not all expected contacts or fields reached the destination. A concrete public example describes a scheduled Metabase-to-HubSpot sync stopping after roughly twenty iterations despite returning around 1,900 source items. It showed an error, so it is evidence of incomplete work rather than proof that all failures look successful. Another operator describes twelve client workflows, poor output visibility and resistance to expensive observability tools. These are detailed self-reports, not verified customer interviews. See C04 and C11 in the evidence register.

**Why now.** Recent agency discussions and company job advertisements show operational ownership alongside automation building. This supports investigating maintenance work, without requiring a market-wide AI adoption statistic. Binalyze, Pyyne and WeTravel advertise related responsibilities.[^20][^21][^22]

**Existing alternatives.** Native n8n logging and retries, native HubSpot sync features, spreadsheets, scheduled comparison scripts, Healthchecks.io, Midwatch, FlowMonix, YieldCue and Solid. There is substantial overlap. This is not an empty category.[^1][^3][^4][^6][^7][^18][^19][^31]

**Proposed difference.** Read the source system and destination system independently, compare individual records against an agreed rule, and attach evidence to each exception. Do not depend exclusively on a successful-workflow signal. The reviewed YieldCue page describes workflow-supplied signals; it does not establish whether the product already offers equivalent independent read-back. A head-to-head trial is required before claiming superiority.[^4]

**Smallest product.** Start with historical CSV exports, then one source connector—Typeform—and HubSpot. Restrict coverage to accepted lead submissions, identity matching and a small number of required fields. Produce an exception queue, review decisions and a downloadable reconciliation report. Initial operation is read-only.

**Business model and proposed price.** Test a $250 fixed-scope audit, credited against a $149/month agency subscription covering up to five client portals and a clearly capped record volume. These are experiments, not validated pricing. Do not advertise unlimited integrations or unlimited hands-on support.

**Distribution.** Founder-led discovery with agencies already maintaining HubSpot integrations; then a small benchmark and anonymized before/after evidence from consenting pilot customers. Ten paying agencies is the first target, not thousands of individual hobbyists.

**Biggest risk.** A native feature or short script already solves the problem cheaply. The new subscription may create more configuration and alerts than it saves.

**Score: 6.5/10.** Tied with the finance alternative after rounding. It ranks first because this team can test the workflow and reach a technical buyer with less accounting and ERP dependency. Confidence is moderate that the problem exists, low that this exact product will sell.

### Second choice: remittance exception preparation for Business Central

**Customer and buyer.** A B2B distributor or service business whose accounts-receivable staff repeatedly match incoming bank payments with invoice details buried in emailed remittances. An AR manager is the user; a controller or finance director is the likely buyer. An ERP implementation partner could be the distribution channel.

**Pain.** A public adviser describes a Business Central client receiving over fifty ACH/wire payments daily and manually retrieving remittance detail. The thread also contains vendor promotion; those replies are not separate buyer validation. Another worker describes ambiguous multi-invoice discounts and deduction handoffs. See C14–C15.

**Why now and alternatives.** Document extraction can help assemble evidence, but commercial competitors already combine rules and AI. SKsoft offers a Business Central cash-application workbench. Monk advertises rules, deterministic matching and model inference. Kolleno markets Business Central integration and publishes a named customer testimonial. No independently verified price comparison or failed incumbent deployment establishes a gap yet.[^13][^14][^15]

**Proposed difference.** Handle one leftover task: prepare a review packet for unmatched payments, linking a remittance line, candidate invoice and discrepancy. Export for the accountant to approve. Avoid claiming to replace the ledger or to know an allocation policy that the business has never defined.

**MVP.** Upload bank CSV, open-invoice CSV and remittance PDFs; extract identifiers and amounts; perform deterministic candidate matching; show evidence and conflicts; export approved mappings. One currency and one customer schema initially. No bank movement or automatic ledger posting.

**Price and distribution hypothesis.** Test a $500 paid diagnostic and $500–$1,000/month if measured processing savings justify it. Approach Business Central implementers and accounting-service firms, asking for their recurring unmatched cases. No outreach has been performed.

**Biggest risk.** Mature competitors or a Power Automate implementation already suffice; each customer requires extensive mapping and support. Missing remittances cannot be reconstructed reliably from nothing.

**Score: 6.5/10.** Potentially stronger economics than the first choice, but weaker current founder access and more domain dependencies. This becomes first choice if the team can access three relevant finance teams and an experienced accounting/ERP partner.

### Third choice: architecture contracts for Python teams

**Customer and buyer.** A Python SaaS team where the CTO or engineering manager wants changes to respect explicit module boundaries. This is much narrower than a tool that claims to understand every developer's code.

**Pain.** Public developers discuss reviewing large changes that pass superficial checks while violating architectural intent. This is qualitative evidence of review burden, not proof that AI universally degrades code or that a separate subscription is wanted. See C19–C21.

**Alternatives.** Import Linter already enforces forbidden imports, layers, protected modules and dependency independence. CodeScene offers commercial code-health and architecture-related analysis, displaying annual-billing prices of €18 and €27 per active author/month for its Standard and Pro tiers.[^11][^12]

**Possible difference.** Help a team extract, approve, version and maintain its architectural rules, with precise PR feedback and an expiry process for exceptions. Reuse existing checking engines where appropriate. The additional workflow must save enough reviewer time to justify a product.

**MVP.** Python-only repository analysis, human-approved module rules, CI enforcement and a documented exception registry. Exclude automatic architecture redesign, all-language support and speculative quality scores.

**Price and distribution hypothesis.** Test $99–$299/month per team through engineering leads and a useful public rule pack. Compare against configuring Import Linter directly. The biggest risk is that onboarding creates a one-time service rather than ongoing product value.

**Score: 5.9/10.** A reserve hypothesis, not a confident build recommendation. Some broad categories score slightly higher but fail the scope or competitive-gap gate.

## Evaluation of the supplied research

The three summaries were not reliably attributed to ChatGPT, Claude and Gemini individually. They are evaluated as Summary A, B and C, in the order supplied. Assigning a model name would invent provenance.

### Summary A: exception management, workflow discovery and crash testing

This summary best identifies concrete operational failure classes. Its strongest idea is exception management after narrowing to a particular business outcome. Its weakest recommendation for this team is broad workflow discovery: collecting events, understanding undocumented work and deploying inside an enterprise are separate hard problems. Celonis already treats discovery as a core capability.[^26]

Keep the focus on incomplete work, review queues and inconsistent data. Discard the implied ranking certainty. Missing elements were a precise buyer, a constrained workflow, the cheap DIY substitute and evidence that the proposed software outperforms products already offered.

### Summary B: reliability, comprehension debt and market statistics

Its strongest contribution is asking what new operational work follows AI adoption. Its code-review concern is worth investigating, but the summary's claim that comprehension debt is fresh and underserved is not established by developer frustration. Paid code-health products and free architecture checkers already exist.[^11][^12]

The weakest recommendation is treating GummySearch's closure as a straightforward opening. Its own announcement says it could not reach a commercial Data API agreement. Replacing the product without solving data access repeats a business dependency.[^24]

The quoted figures require correction:

- **“88% of agent pilots never reach production”: not independently verified.** Search found secondary repetitions, not a reliable primary study with an applicable denominator and methodology. Do not use this in a pitch or financial model.[^33]
- **“$340K lost per pilot”: not verified.** No reliable supporting primary source was established. Remove it rather than trying to turn another spending or savings figure into a loss estimate.
- **“94% of enterprises have agents that cannot connect”: mischaracterized.** OutSystems reports concern about sprawl among surveyed organizations, based on 1,900 IT leaders. Concern is not demonstrated broken interoperability or a purchasing commitment.[^23]
- **“11K hiring applications per minute”: not verified here.** It plays no role in the recommendation.

The curl example also needs updating. Its bounty closure is a real event, but a later firsthand account describes a rise in high-quality reports and the burden of verifying and fixing them. A product that simply flags AI-written reports would target the wrong property.[^29][^30]

### Summary C: rollback, code decay, permission leakage and visual testing

This summary is technically specific but too optimistic about generic infrastructure. Its strongest idea for this team is explicit architecture enforcement, provided a paid gap beyond existing tools is demonstrated.

“Single-click rollback” is its most dangerous simplification. Restoring a workflow definition is not undoing an email, refund or external database mutation. Compensation requires application-specific operations and can fail. Temporal's published guidance already describes explicit compensation patterns.[^28]

The visual-testing premise also overstates the weakness of Playwright. It supports role, text, label and explicit test-ID locators, as well as automatic waiting and retries. AI-generated UI does not automatically invalidate those methods. Visual testing may be useful, but brittle CSS alone is not differentiation.[^25]

Permission-aware retrieval is important, but Oso's existing authorization work illustrates active competition. A three-person team would also need customers to trust a new system with sensitive access decisions.[^27]

### Overall assessment

Summary A is most useful for narrowing the problem, Summary C for identifying technical boundaries, and Summary B least reliable as presented because of unsupported numbers and optimistic market-gap claims. This is a ranking of the supplied summaries, not a judgment of the models that may have produced them.

“Reliability after AI adoption” is a reasonable search direction. It is not itself a product, a defensible market or a guarantee of an accessible buyer.

## The selected product in detail

### 1. The job the customer hires it to do

At a chosen cutoff, answer: **Which accepted lead submissions have not reached the required destination state, and what evidence tells us that?**

Consider an illustrative agency client. Its form received 100 submissions. Eight are intentional exclusions under the client's rules. Of the remaining 92, eighty-eight are verified in HubSpot, two are confirmed discrepancies after the waiting window, and two cannot yet be checked because the connector is unavailable. The tool must show all four categories. It must not report “92 succeeded” from run status, or call the two unknown cases lost leads.

This example is invented to explain the proposed behavior; it is not a customer result. A second check can identify incorrect required fields or an unresolved duplicate identity. It cannot determine whether a free-form sales email was persuasive or whether an uncontacted prospect would have purchased.

### 2. Why an agency is the initial customer

An agency repeatedly configures similar handoffs and may carry the cost of client incidents. The owner can compare subscription cost with maintenance work and retainer margin. Public job postings show employers assigning ongoing operation and quality monitoring, while agency complaints show the pain of finding failures downstream.[^20][^21][^22]

The weak point is budget. Some operators explicitly view existing monitoring as excessive. We should exclude hobbyists and agencies that only deliver one-off workflows and have no maintenance obligation. A company having the problem does not establish that an agency controls the purchase or has permission to expose client records.

### 3. Current workaround and why it may be enough

Customers can inspect execution logs, receive error notifications, add required-field checks, reconcile exports or write a scheduled comparison job. HubSpot itself has sync functionality and record-level integration status for supported integrations.[^7][^18][^19]

These solutions may already be sufficient. The proposed benefit is reducing repeated configuration and review across clients while identifying the exact unresolved records. If each workflow only fails once during setup and stays healthy afterward, sell a one-time audit or recommend the native fix. Do not force a subscription around a solved problem.

### 4. Competitive test, including the closest substitutes

**Healthchecks.io:** free monitoring for twenty jobs and a $20/month Business tier provide a low price anchor for missing-run detection. A heartbeat is a powerful substitute when the question is simply whether a scheduled job completed.[^6]

**Midwatch:** advertises silent-stop, low-output and configuration-drift monitoring, plus agency reporting. Its published prices are $49/month for Solo and $197/month for Agency. Multi-client dashboards and reports are therefore not a unique selling point.[^1][^2]

**FlowMonix:** advertises incident grouping, explanations and retries; its page lists a free tier, $29/month Pro and $99/month Team. “Explain the error with AI” is already available as a proposition.[^3]

**YieldCue:** directly markets outcome monitoring, configured checks and evidence-bearing incidents across automation tools. Its listed monthly prices are $19, $99 and $299. This is the nearest conceptual competitor. The reviewed product page relies on supplied workflow signals; equivalent direct source/destination verification remains an unanswered capability question, not a proven omission.[^4][^5]

**Solid:** advertises HubSpot record reconciliation and sync repair. Its breadth could cover the proposed job. Pricing, implementation effort and actual accuracy were not verified. It belongs in customer comparisons, not in a footnote that can be ignored.[^31]

**Native HubSpot and n8n:** strongest alternatives where their connector coverage matches the customer. Test these first. An agency should not buy a new system to recreate a built-in report.[^7][^8][^18][^19]

The first competitive benchmark must use the same customer dataset and agreed rules. Compare manual minutes, correct actionable discrepancies, false alarms, unsupported cases and ongoing setup effort. Competitor landing pages were reviewed; the products were not installed or benchmarked. No claim that competitors “cannot do this” is warranted yet.

### 5. Scope of a 4–8 week MVP

The timing is an engineering estimate conditional on three available founders, timely sandbox/API access and a stable customer mapping. Production security requirements, provider approvals and custom integrations can extend it.

1. Import source submissions and HubSpot exports. Capture the extraction time and declared coverage window for each.
2. Configure a small set of explicit rules: which submissions should arrive, how identity is matched, which fields matter and the waiting window.
3. Compare records deterministically. Present verified matches, confirmed discrepancies, documented exclusions and unknown/unobservable items separately.
4. Review exceptions with source evidence, destination evidence, timestamps and an owner. Keep a history of decisions.
5. Generate an export that the agency can use to repair the original workflow. Initial product performs no automatic replay, contact merge or customer messaging.
6. Add Typeform polling and HubSpot read access only after the export-based comparison proves useful. Keep a coverage watermark and connector-health state.

The first workflow is new-lead intake, with a defined policy for existing contacts and repeat submissions. Do not equate one submission with one new contact: an existing contact may be a legitimate outcome. A lead's email alone is not a universal event identifier. Repeated submissions, changed emails, merged contacts and missing identity must be resolved explicitly or marked unsupported.

Checking a record now does not prove that it had the same fields at submission time. Historical claims require property history or a captured state, and causal claims require stronger correlation. The first product reports observed state at a stated cutoff.

### 6. A technical constraint that changes the product promise

Typeform's Responses API says very recent submissions—approximately the last thirty minutes—may not appear. HubSpot documents search indexing delays. A read-only polling approach cannot honestly guarantee detection within seconds.[^16][^17]

Start with hourly reconciliation of a completed window, using a configurable delay and overlapping reads. This is an operational target, not a guaranteed upper bound on provider latency. Missing source data or an API outage must cause “coverage incomplete,” not a green success. Optional direct webhook notifications can improve early awareness later; independent polling remains necessary to detect missing webhook delivery.

The value proposition is earlier discovery than occasional manual checks or client complaints. Customers requiring immediate response protection may need a different source/integration design and are outside the initial promise.

### 7. Implementation responsibilities

Use a small API service, a durable relational database and background workers. Python/FastAPI is a plausible choice for a team familiar with it, but the actual founder stack has not been verified. PostgreSQL should retain the canonical observations and review state. A queue dispatches work; it must not be the only record of unfinished checks.

Persist source event IDs where available, connector watermarks, rule versions and evidence timestamps. Use tenant-scoped keys, bounded retries and an independent watchdog. API throttling, pagination and token revocation should degrade coverage visibly. A failed check must not become a false customer-data mismatch.

Founder one owns connectors and source completeness. Founder two owns matching, evidence and review state. Founder three owns the user workflow, customer discovery and measurement. These are suggested responsibilities, not assignments to identified people.

Before a live pilot, verify isolation between clients, minimum access scopes, encrypted credentials, deletion/retention behavior and secret redaction. The buyer must have authority to share the relevant client data. Do not collect every payload by default. These are product requirements for this data-handling workflow, not a claim of completed certification.

### 8. Where AI actually helps

AI can suggest a field mapping or summarize evidence for an operator. The operator approves the mapping. Matching identities, counting items, applying exclusions and determining whether a field meets an exact rule should use deterministic logic.

The core product should work if all model calls are disabled. This is an advantage: adding AI is justified only when it reduces setup or review time without worsening reliability. A low AI-leverage score is acceptable for a valuable SaaS.

### 9. Pricing and economic test

Start with a proposed $250 audit of one defined handoff and a $149/month subscription for up to five portals, initially capped at 10,000 submissions/month. Confirm whether that usage envelope is commercially meaningful; it is not derived from observed customer volumes.

Illustrative economics: if a qualified agency avoids eight hours of checking monthly and values that capacity at $40/hour, the gross capacity value is $320/month. At $149 the benefit is only about 2.1 times the subscription, before residual effort. If it saves two hours, the same product costs more than the $80 of capacity recovered. These inputs are assumptions to replace with customer measurements. Saved capacity is not automatically reduced payroll or added revenue.

At $149/month, ten agencies yield $1,490 MRR and one hundred yield $14,900 MRR, before churn, costs and taxes. At a hypothetical $30 of infrastructure and support cost per account, contribution is about 80%; at $100 it is only about 33%. This excludes founder salary and acquisition costs. It shows why custom support can break the model, not what margins will be achieved.

Do not justify pricing with the face value of “lost leads.” To claim recovered gross profit, a customer would need to establish eligibility, incremental conversion and contribution margin. Initially price against measured review time and incident handling.

### 10. First ten and first hundred customers

Build a prospect list of forty agencies that visibly maintain HubSpot and custom automation work. Use public agency directories, partner listings and technical case studies. Qualify actual maintenance ownership and source access; a generic AI-agency label is insufficient.

The discovery offer is: “Show us your last incomplete handoff and how you checked it. We will compare one agreed source window with HubSpot and show every mismatch and unknown.” Ask for consented exports or a supervised walkthrough, not unrestricted credentials.

Ten customers are an objective, not a promised conversion funnel. Record contacted accounts, responses, interviews, paid audits, pilots, conversions and declines. After early results, pursue referrals from implementation partners and publish a small evaluation pack showing the limitations as clearly as the successes. Do not post invented ROI case studies.

For one hundred customers, onboarding must work repeatedly for the same source/destination patterns without a founder repairing every mapping. Standardized connectors, reusable check templates and agency referrals could support that. Paid ads and broad enterprise sales are not the initial strategy.

Draft outreach is provided in the review brief. No emails, DMs, forms or sales conversations have been sent.

### 11. Defensibility and expansion

There is no strong moat on day one. A comparator and review queue are easy to imitate. A possible advantage develops from trusted connector behavior, customer-approved outcome definitions, documented exception patterns and distribution through agencies. Customer data cannot simply be pooled to train a shared system without permission.

If retention is demonstrated, expand from lead intake to another handoff that the same buyer owns, such as approved quote-to-CRM updates. Only later add gated recovery actions. Each action needs fresh-state validation, an idempotency strategy and explicit authority. A three-to-five-year expansion could be a system of record for business handoff exceptions, but that is a direction, not a forecast.

### 12. The biggest reason this could fail

The customer agrees the problem exists but does not need a new vendor. Basic validation prevents the failures, native sync provides enough visibility, or a contractor writes the comparison once. If the remaining mistakes are semantic—an agent chooses the wrong policy or sends a misleading reply—record reconciliation will not solve them. The narrowness that makes this buildable also limits the addressable problem.

## Evidence quality and scoring

The accompanying register contains **25 observations across 24 distinct URLs**, not 25 verified companies or purchasing decisions. C12 and C13 are separate commenters in the same discussion. The register marks one named firsthand account, twenty-one detailed public self-reports, and three weaker items involving promotional framing, a removed original post or an inaccessible original page. Identity and employment have not been independently verified.

Each observation includes a pain score, recurrence hypothesis, willingness-to-pay hypothesis, competitive headroom and buildability score. These are analyst prioritization judgments. Observed frequency is recorded separately; an invented monthly incident count is never substituted for missing data.

Evidence primarily comes from n8n and other user forums, Reddit, official product/documentation pages, public job advertisements, a LinkedIn post and indexed HN discussion. X searching produced no usable result. YouTube, G2/Capterra, Product Hunt and authenticated community accounts were not systematically audited. The result is a focused desk-research assessment, not an exhaustive census of social media or buyers.

Nineteen distinct supplied or narrowed proposals are scored across fifteen factors in `scorecards.json`. Weights total 100: pain 10, frequency 7, economic value 10, willingness to pay 12, buyer clarity 8, market size 5, competitive headroom 4, gap 8, differentiation 6, buildability 10, distribution 8, retention 5, defensibility 4, AI leverage 2 and timing 1. Higher is better throughout; competitive headroom means less difficult competitive pressure.

Overall score is the weighted sum divided by 100. Values are displayed to one decimal, but differences of a few tenths have little meaning without buyer evidence. The market-size score reflects relative breadth only; no defensible numeric TAM for the chosen narrow segment was established. It should be replaced by a count of reachable, qualified agencies and their measured budgets.

The top two tie at 6.5. Reducing the lead-reconciliation willingness-to-pay score by two points lowers its total by 0.24; raising finance distribution by two points raises that alternative by 0.16. The ranking is not robust enough to justify ignoring real founder access. Conditional gates override arithmetic: a universal rollback platform does not become buildable because its theoretical loss-prevention value is high.

## Ideas that sound good but should be rejected in their current form

- **Generic agent reliability platform:** too many failure classes and strong overlap with evaluation, observability and orchestration tools. Narrow to a business handoff first.
- **Universal rollback:** cannot promise reversal of arbitrary external effects. A provider-specific recovery product would need its own customer and safety case.
- **Another generic crash-test dashboard:** existing evaluation platforms already support datasets, stubs and step-level analysis. Require a demonstrably underserved workflow before rebuilding them.
- **Generic code explanation or architecture score:** explanations are easy to produce; a team must show why existing code health and static checks fail its needs.
- **GummySearch clone without a viable data agreement:** repeats the central platform risk identified by the original service.
- **AI-authorship detector for security reports:** authorship does not determine whether a report is correct. Reproducibility and triage capacity are the actual jobs.
- **General-purpose hiring verification:** insufficient direct buyer evidence in this study; no recommendation based on the unverified application-volume statistic.
- **Whole-enterprise workflow discovery, permissions or legacy UI layer:** defer for a team without enterprise access, deployment experience and a narrowly defined gap.
- **“Startup tools for startups” as a category:** no identifiable recurring job, budget or differentiated workflow was supplied. It is an audience label, not a serious product proposal.

## First thirty days and decision gates

### Days 1–7: test the buyer and the recent incident

Create forty qualified agency prospects and attempt at least twelve substantive discovery conversations. Ask for the most recent actual missing/incorrect handoff, the source and destination, who discovered it, how it was repaired, time spent, existing monitoring and who pays for maintenance. “Sounds useful” is not a positive result.

Proceed only if at least five conversations establish repeated review work or recent consequential incidents in the target workflow. Seek three consented, representative export sets. Record non-buyers and straightforward configuration fixes, not only enthusiastic respondents.

### Days 8–14: compare records and alternatives

Run manual or lightweight read-only audits before building a platform. Define expected outcomes with the customer, include intentional exclusions and hold back a set of cases from configuration. Compare native tools, a simple script and the closest available competitor on the same agreed task.

Target at least two paid $250 audits. This threshold is an internal stop rule, not a statistically validated market estimate. If no one provides usable data, treats the problem as recurrent or accepts a paid diagnostic after qualified conversations, stop the product build and investigate why.

### Days 15–21: prove usefulness in shadow mode

For willing customers, run a narrowly scoped prototype that reads data and produces reviewable exceptions. Measure precision, known-case recall, coverage and human time. A successful prototype must not quietly omit API failures or unsupported identities from the denominator.

Proposed acceptance targets: at least 95% actionable-alert precision on adjudicated items; detection of every deliberately seeded deterministic failure in the agreed test set; explicitly reported coverage for all eligible source records; and at least 50% reduction in the agreed manual checking task. These are test targets, not achieved results. Seeded-test recall is not real-world recall.

### Days 22–30: test whether it earns a subscription

Ask for a paid ongoing pilot on stated terms, not a non-binding compliment. Aim for two agencies willing to pay $149/month, with an identified person using the exception workflow. Measure setup time; a target of two founder-hours for a supported handoff is an assumption to test.

Proceed toward a 4–8 week MVP only if customers pay, provide access, confirm an advantage over the baseline and accept the product's coverage limits. If the offer only creates value during initial cleanup, sell a service or stop. Thirty days can establish early paid interest; meaningful retention still requires later renewals, ideally at least two cycles before aggressive expansion.

### Explicit kill conditions

Stop or change the idea if native features or a simple script solve the same task at similar effort; if customers mostly need semantic judgment rather than record verification; if source completeness cannot be established; if paid buyers cannot grant access; if recurring support consumes the subscription margin; or if alerts regularly flag legitimate exclusions and indexing delays as failures.

## Reality check

1. **Will a company pay today?** Insufficient evidence for this specific product. Adjacent paid offers and detailed pain reports justify a paid test.
2. **Who signs?** The agency owner or accountable automation lead, if the agency controls its maintenance tooling. Client approval may still be necessary for data access.
3. **Which budget?** Agency software/operations spending or a client's existing integration-maintenance retainer, not a speculative “AI transformation” budget.
4. **What if they do nothing?** Some continue manual checks or discover failures downstream; some suffer little because their workflows are already reliable. Qualify which situation applies.
5. **How much financial pain?** Not measured. Obtain actual handling time, rework and credits; distinguish capacity from cash and missed records from proven lost sales.
6. **Why has an incumbent not already won?** That has not been established. Several incumbents and small competitors may already solve the customer's specific case.
7. **Why could a small team win?** Faster setup for one repeated handoff and clearer record evidence through an accessible agency channel, if customer comparison confirms it.
8. **Largest technical risk?** Incorrect matching or incomplete observations make the verifier itself untrustworthy.
9. **Largest distribution risk?** Agencies acknowledge pain but will not add a recurring subscription or grant client data access.
10. **What would disprove the thesis?** Good native/DIY coverage, little recurring manual effort, no paid diagnostic demand or customers primarily reporting out-of-scope semantic mistakes.
11. **What should be validated before serious code?** Buyer ownership, recurring task frequency, usable source records, comparison baseline, allowable data access and a paid commitment.
12. **What happens first?** Customer incident interviews, consented export audits and a benchmark against the cheapest adequate alternative.

## Sources

The companion evidence register provides the original discussion links for C01–C25. Numbered references below support product capabilities, price observations and corrections. Vendor capability claims and customer testimonials were not independently benchmarked. Job listings show hiring intent, not confirmed hires or a transferable software budget.
