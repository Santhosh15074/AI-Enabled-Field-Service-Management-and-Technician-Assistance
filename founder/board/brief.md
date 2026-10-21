# Board brief: AITechnician (working name)

## The idea (from founder/idea.md)

- What it is: AI-assisted field service management (FSM) software that sorts customer complaints by urgency, suggests quick fixes, turns technicians' spoken reports into service records and flags equipment likely to fail.
- Who it is for: small service companies in Chennai, India, with roughly 5 to 50 field technicians that repair ACs, appliances, generators or electrical systems.
- What it sells, at what price: a web app with three portals (customer, technician, admin). **The price and pricing model are undecided** (the founder said "I don't know").
- Where and how: Chennai first, India only. Delivered as a web app. **The sales and acquisition channel is undecided.**
- Budget and constraints: to be built out after the founder finishes an MCA (Master of Computer Applications) degree, alongside a day job. India only. **Budget not stated.** The founder listed "having a first customer lined up through work or family" as a constraint, but it is **not confirmed** whether such a customer actually exists.

## What already exists

A working prototype, built as the founder's MCA final-semester academic project (solo build):

- **Stack:** Python FastAPI backend, PostgreSQL, scikit-learn models, React/TypeScript frontend. Runs locally; not yet deployed or used by any real business.
- **Customer portal:** customers sign up with a phone number, register their equipment, raise complaints, try suggested quick fixes before a visit, track requests and read service reports.
- **Technician screens:** see assigned jobs, update status, view suggested fixes, record sensor readings, dictate service reports by voice (browser speech-to-text).
- **Admin screens:** raise requests for customers, assign technicians, manage staff, maintain the troubleshooting knowledge base, watch failure predictions, view analytics and notifications.

### The four AI components and their measured performance (from the founder's own evaluation)

| Component | Test data | Result | Baseline |
|---|---|---|---|
| Urgency classifier (sorts complaints low/medium/high) | 3,268 held-out support tickets | 62.2% accuracy, 65.8% recall on high urgency | Majority class: 40.5% |
| Failure prediction (from sensor readings) | 2,000 held-out readings, 68 failures | ROC-AUC 0.958; catches 75% of failures at "critical" level | Random PR-AUC 0.034 vs 0.774 |
| Troubleshooting assistant (matches complaint to a knowledge-base fix) | 40 hand-written complaints, 20 knowledge-base entries | 90% top-1, 100% top-3 | Keyword search: 77.5% top-1 |
| Report extraction (voice/text report to structured record) | 12 hand-labelled reports | Action and time 100%, issue 91.7%, parts 88.9% recall | none |

The founder's own documented limitations: the urgency model was trained on IT-helpdesk tickets and the failure model on synthetic milling-machine data, not on real AC/appliance/generator service data. The troubleshooting and extraction test sets are small and were written by the same person who wrote the knowledge base. Every AI output is advisory and reviewed by a person.

## Open facts nobody has yet

- Price and pricing model.
- How many target companies exist in Chennai, what they use today (paper, WhatsApp, Excel, existing FSM software) and what they pay for it.
- Competitors and their prices (to be answered by /founder-competitors).
- Whether target customers would pay, and how much (to be answered by /founder-consumer and /founder-pricing).
- Cost to acquire a customer, cost to host and support, and the founder's budget (to be answered by /founder-cfo).
- Whether the target equipment (ACs, appliances, generators) actually produces sensor readings the failure model can use.
