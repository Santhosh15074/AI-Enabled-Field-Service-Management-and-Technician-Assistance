# Offer: the AITechnician Founding Shop Plan

Built 2026-10-19 with the Offers lens (value equation, problem list, stack). Inputs: `idea.md`, `board.md`, `competitors.md`, and the 20-buyer panel in `panel-v1/results.md`. **`numbers.json` does not exist yet** (`/founder-cfo` has not run), so every cost below is a rough estimate with its assumption stated, not a CFO number.

## 1. The problem list (in the buyer's words)

Sources: **P** = panel v1 objection, **C** = competitor complaint or substitute pain, **B** = board condition.

**Before buying**
1. "I've never heard of you; nobody I know uses it." (P, the top reason to pass, 6 of 20)
2. "Will a one-person company still be around next year?" (P, B)
3. "If it shuts down, my job and AMC records are stuck." (P)
4. "Is my customer list safe?" (P)
5. "WhatsApp is free and works well enough." (P, 5 of 20; C)
6. "₹199 a head is double the ₹99 apps." (P, 3 of 20; C: TeamShastra ₹99)
7. "Per-technician pricing means the bill grows every time I hire." (P)
8. "Pricing that changes with volume is hard to predict." (C: Zoho appointment bundles)
9. "My brand jobs already go into the brand's system; this would be double entry." (P)

**During**
10. "My technicians will stop pressing the button after a week." (P, raised by nearly every buyer)
11. "They barely read English." (P)
12. "Will it understand Tamil and Tanglish on a noisy rooftop?" (P)
13. "A wrong report going to my customer on WhatsApp hurts my name." (P)
14. "No time to set it up during the April–June rush." (P)
15. "Setup takes effort, and these apps are rigid." (C: Zoho reviews)
16. "Cluttered technician app that needs a constant connection." (C: Zoho reviews)
17. "I'll be chasing them on two apps instead of one." (P)

**After**
18. "Customers still argue about which part was changed." (P, C: no written record on WhatsApp)
19. "AMC renewals lapse because nobody sent the reminder." (P, C)
20. "Will I actually get my evenings back?" (P)
21. "Who do I call when it breaks?" (P)
22. "Does the price jump once I'm locked in?" (raised in the re-test, P011)

## 2. Solutions, scored

Value = to the buyer (1–5). Cost = to deliver (1–5, **estimated**, CFO to confirm).

| # | Solution | Answers | Value | Cost | Keep? |
|---|---|---|---:|---:|---|
| A | **Pay only if they use it**: first month free; billing starts only if ≥7 in 10 jobs went through the app in the trial's last 2 weeks | 1, 2, 5, 10, 17 | 5 | 2 | **Core guarantee** |
| B | **Owner or technician approves each report with one tap** before WhatsApp sends it | 13, 12 | 5 | 1 | **Core** |
| C | **Photo of the old part** attached to the report | 18 | 4 | 1 | **Core** |
| D | **Flat price for each shop**, by size band | 6, 7, 8 | 4 | 1 (but see the WhatsApp cost below) | **Core** |
| E | **Your data stays yours**: Excel export any time, full copy on exit | 3 | 4 | 1 | **Bonus** |
| F | **In-person setup by the founder** in the quiet months, plus a direct phone number | 1, 2, 14, 15, 21 | 5 | 3 (founder time; caps capacity) | **Bonus** (and the real reason for the scarcity) |
| G | **Price fixed for two years** for founding shops | 22, 2 | 3 | 2 (gives up future price rises) | **Bonus** |
| H | AMC renewal reminders sent automatically | 19 | 4 | 2 (per-message cost) | Core feature |
| I | Voice in Tamil, English or a mix, one button, no typing | 11, 12, 16 | 5 | 4 (build and per-minute cost unknown) | Core feature, **not built yet** |
| J | Written data-privacy promise (customer data never shared or sold) | 4 | 4 | 1 | **Add** (found in the re-test, P015) |
| K | Live rooftop demo on one of their own technicians during setup | 12 | 4 | 1 | **Add** (asked for in the re-test, P002) |
| L | Write jobs into the brand's own system too | 9 | 4 | 5 (every brand's system differs) | **Drop.** Brand service partners are not the first market |
| M | Referrals from existing shops | 1 | 5 | 0 | **Cannot offer honestly yet.** It becomes possible after the first shops; never invent one |

## 3. The stack

**Name:** *AITechnician Founding Shop Plan*

**Core (the outcome, not the parts):** your technicians say what they did, in Tamil or English, and the customer gets a checked service report with a photo of the old part on WhatsApp. You stop phoning technicians all day and writing up jobs at night.

**Price:** flat for each shop. **₹999 a month for up to 10 technicians, ₹2,499 for up to 25, ₹4,499 for up to 50.** No setup fee, cancel any time. These are test prices: per technician they come to about ₹100–250 at 10 technicians, ₹100–230 at 25 and ₹90–170 at 50. The final price comes from `/founder-pricing`.

**Bonuses (each answers one objection):**
1. *Set up in person by the founder before the rush, with a direct phone number.* Answers "who are you" and "no time in summer".
2. *Your data stays yours:* export to Excel any time, a full copy on exit, and a written promise not to share it. Answers lock-in and privacy.
3. *Founding-shop price fixed for two years.* Answers "the price jumps once I'm in".

**Guarantee:** *you pay nothing until your team is using it.* The first month is free, and billing starts only if at least 7 in 10 jobs went through the app in the last two weeks of that month. Because it is measured from the app's own job counts, it can be checked. It is a condition for starting to pay, not a refund promise, so nothing is clawed back later.

**Scarcity and urgency (true only if you commit to them):**
- **10 founding shops.** This is a real capacity limit: a founder with a day job can only set up and support so many shops in person.
- **Set up in the quiet months before the summer rush.** The April–June rush is real. It also means Tamil voice, WhatsApp sending and AMC reminders must work **before about March 2027**. If they won't, change the dates. Don't fake the deadline.

## 4. What the stack costs (rough, for `/founder-cfo` to replace)

> **Superseded by `cfo.md`.** Meta's own India utility rate is about ₹0.115 a message, not ₹0.50, so WhatsApp is about ₹72 a month for a small shop. The bigger costs are Tamil speech-to-text (about ₹312) and AI structuring (about ₹156). The table below is kept as first written.

| Item | Estimate | Assumption |
|---|---|---|
| WhatsApp message per report | **₹0.50** per utility conversation | RichAutomate's published "SaaS Pay" rate ([source](https://richautomate.in/blog/best-whatsapp-business-api-for-ac-appliance-repair-india-2026)). Meta's current India rates need checking |
| WhatsApp cost, 10-technician shop | ≈ **₹390 a month**, about 40% of the ₹999 price | **Assumes** 3 jobs per technician a day × 26 days = 780 reports. Jobs per day is a guess; ask real owners |
| WhatsApp cost, 50-technician shop | ≈ ₹1,950 a month (43% of ₹4,499) | same assumption |
| Speech-to-text for Tamil | **unknown** | depends on the provider and minutes per report |
| Setup visit | founder time, probably half a day per shop | a guess. It sets the 10-shop limit |
| The guarantee | a failed trial costs one setup visit + one month of messages and speech-to-text, and brings in no revenue | the claim rate is unknown. If half the trials fail, every paying shop also carries the cost of one failed setup |

**This is the finding to take to the CFO:** a flat ₹999 price with per-message WhatsApp costs may leave a thin margin on small shops. Options: fewer messages (send one report per job, not updates), a higher small-shop tier, or charging AMC reminders separately. The guarantee can't be confirmed as affordable until `/founder-cfo` runs.

## 5. Value equation, before and after (1–10)

| | v1 pitch | Founding Shop Plan | What moved it |
|---|---:|---:|---|
| Dream outcome | 6 | 7 | Photo of the old part settles disputes; "your evenings back" made explicit |
| Perceived likelihood | 2 | 5 | Pay-only-if-used guarantee, one-tap approval before sending, live demo. **Still no references**, so it stays at 5 |
| Time to result | 5 | 6 | Set up before the rush; the report goes the same day |
| Effort and sacrifice | 4 | 7 | Founder sets it up, flat price, no lock-in, data export, no risk of paying for an unused app |

## 6. Re-test: the same 20 buyers (seed 956266)

| | v1 (₹199 per technician) | Founding Shop Plan |
|---|---:|---:|
| **Buy** | **4 of 20 (20%)** | **14 of 20 (70%)** |
| Pass for trust | 6 | 3 |
| Pass for habit | 5 | 3 |
| Pass for price | 3 | 0 |
| Pass for timing | 1 | 0 |
| Pass for need | 1 | 0 |

10 buyers flipped to yes and none flipped to no. By group: small shops went from 27% to 82%, owners who had tried an app before from 0 of 2 to 2 of 2, and owners who run on WhatsApp from 1 of 6 to 5 of 6.

**Read this carefully: the 70% is mostly "I'll try it, since it's free and risk-free".** The guarantee shifts the risk from the buyer to the founder. Nearly every yes still says *"I'm not promising to keep paying"* and still doubts that technicians will keep pressing the button. So the offer moved the decision from **day 0 to day 30**. The real conversion is the share of trials that reach 7 in 10 jobs, and only real shops can answer that.

**What didn't move:**
- **The 3 owners who buy only on a recommendation all still pass.** Only a real reference fixes this: *"I'm not going to be one of the first ten to test it."* (P001)
- **Owners loyal to WhatsApp who doubt their team will reach the 7-in-10 bar** (P006, P007).
- **Brand service partners**, because of double entry (P009). Dropped from the target on purpose.

**New objections the re-test surfaced:**
- Will the founder answer the phone during the rush? (P001, P010)
- Customer-data privacy (P015). Now answered by item J.
- A price jump after the two-year lock (P011).
- Proof of Tamil on a rooftop at setup (P002). Now answered by item K.

## 7. Before promising any of this

- [ ] Run `/founder-cfo`: WhatsApp and speech-to-text cost per report, setup time, and the cost of the guarantee at 30%, 50% and 70% failed trials.
- [ ] Confirm that Tamil voice, WhatsApp sending, one-tap approval and AMC reminders can be built and tested before the dates in the pitch.
- [ ] Write the data-privacy promise and the export process (item J) before the first setup, and check them against India's DPDP Act. This is not legal advice.
- [ ] Decide what "10 founding shops" means for your own time, and stick to it.
- [ ] After 2 or 3 real shops reach day 30, ask their owners whether they'll take calls from other owners. That is the only honest answer to the recommendation buyers.
