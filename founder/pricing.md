# Pricing: AITechnician Founding Shop Plan

Set 2026-10-19 from three things you can check:
- what the simulated buyers said (`pricing-curve.md`, re-test panel in `panel/`);
- what competitors charge (`competitors.md`);
- what the business needs to earn (`cfo.md`, `numbers.json`).

**The buyer answers are simulated.** They pick what to test, not what is proven.

## 1. The price

**Starter: ₹1,499 a month for up to 10 technicians, including 750 reports a month.** The price is flat for the shop and excludes 18% GST.

Why ₹1,499:

- **Buyers.** The 11 small-shop buyers on the panel give an acceptable range of **₹306 to ₹2,000**. The point where as many call it a bargain as call it expensive is ₹801. Their median "getting expensive, but I might still buy" is **₹1,500**, and their median "too expensive to buy" is ₹2,500. At ₹1,499, 3 of 11 already find it expensive and none find it too expensive. **₹1,499 sits at the top of the comfortable zone.** It is a stretch price, not a safe one, which is why section 4 tests it against ₹999.
  - Note: the panel answered about the ₹999 pitch. Nobody has seen ₹1,499 yet.
- **Competitors.** For about 8 technicians:
  - [TeamShastra](https://teamshastra.com/pricing) costs about ₹792 (₹99 a user).
  - [Quick Assign](https://www.capterra.in/software/1079342/Quick-Assign-Service-CRM) costs ₹699 flat.
  - [Zoho FSM](https://help.zoho.com/portal/en/kb/fsm/getting-started/articles/fsm-pricing) Standard costs US$30 for 60 appointments.

  ₹1,499 is about twice the Indian job apps. **It only holds if the voice-to-report-on-WhatsApp result is visibly different from a typed job app.** That is the price objection buyers raised (section 5).
- **Margin** (CFO tool at each price, Starter shop of 8 technicians at 3 jobs a day):

| Price | Contribution per shop | Break-even (paying shops) | Year 1 operating profit | Cash needed |
|---:|---:|---:|---:|---:|
| ₹999 | ₹433 (43%) | 14 | -₹39,822 | ₹94,246 |
| ₹1,199 | ₹633 (53%) | 10 | -₹26,622 | ₹82,939 |
| ₹1,299 | ₹733 (56%) | 8 | -₹20,022 | ₹79,500 |
| **₹1,499** | **₹922 (62%)** | **7** | **-₹7,548** | **₹74,962** |

At ₹999 you need 14 paying shops to break even, against a plan of 11. At ₹1,499 it is 7, and the business makes money every month from about month 8. **Below ₹1,199 the plan doesn't work** unless costs fall.

**Why 750 reports:** each report costs about ₹0.87 (speech ₹0.50, AI ₹0.25, WhatsApp ₹0.115; see `cfo-sources.md`). On a flat price, a very busy shop could cost more than it pays. 750 covers 8 technicians at about 3.6 jobs a day. At the full 750 a Starter shop still leaves about ₹815 (54%).

**Predictable bills**, because Zoho reviewers complained that pricing by appointment was hard to predict:
- There are **no overage charges**.
- If a shop goes over its limit two months in a row, you call them and move them up a tier, with a month's notice.

## 2. The ladder

| | **Starter** | **Growth** | **Pro** |
|---|---|---|---|
| Technicians | up to 10 | up to 25 | up to 50 |
| Reports a month | 750 | 2,000 | 4,000 |
| Price a month (before GST) | **₹1,499** | **₹2,999** | **₹5,999** |
| Per technician at full size | ₹150 | ₹120 | ₹120 |
| Contribution at the report limit* | ≈ ₹815 (54%) | ≈ ₹1,198 (40%) | ≈ ₹2,397 (40%) |
| Panel range for this size | ₹306–2,000 (11 buyers) | ₹517–3,995 (6 buyers, thin) | not enough answers (3 buyers: "getting expensive" at ₹4,500–7,500) |
| Reason to step up | — | more technicians and reports; a login for the office coordinator | more technicians and reports; logins for several office staff |

\*Worked out by hand from ₹0.865 per report plus 2.36% gateway fees, not run through the CFO tool. The CFO tool has only modelled Starter. Growth and Pro sit inside or near what those buyers said, but the samples are too small to trust.

Every tier includes the same core:
- Tamil, English or mixed voice reports;
- one-tap approval before sending;
- a photo of the old part;
- WhatsApp delivery;
- AMC reminders;
- Excel export.

**Size is the only thing that changes between tiers.** Buyers asked for simplicity, so there are no feature gates.

## 3. The opening offer

**Founding shops (the first 10, or until 31 March 2027, whichever comes first):**
- **The first month is free.** Billing starts only if at least 7 in 10 jobs went through the app in the last two weeks of that month.
- **The price is fixed for two years** at the tier price above.
- **The founder sets up the shop in person** before the summer rush.

**There is no discount and no "was ₹X" price.** The founding benefit is the price lock, the in-person setup and the guarantee, so buyers aren't trained to wait for a cheaper deal. The end date is real: it is the quiet season before the April–June rush, and only if Tamil voice and WhatsApp delivery are working by then (see `offer.md`). If they aren't, move the date. Don't keep a fake deadline.

## 4. What to test with real buyers

Two prices inside the small-shop range: **₹999 and ₹1,499** for Starter.

**How:**
1. **Split the founding-shop conversations.** For the first 10 to 12 owners you visit, alternate the price you quote: odd-numbered visits hear ₹1,499, even-numbered visits hear ₹999. Use the same pitch, same demo and same guarantee.
2. **Record for each owner:**
   - whether they agree to the free trial;
   - the price objection they raise, word for word;
   - whether they pass the 7-in-10 bar at day 30;
   - **whether they pay in month 2.**
3. **Use only what owners actually do.** If ₹1,499 converts from trial to paid at no less than about two-thirds the rate of ₹999, it earns more (the contribution is more than twice as large). Shops that started at ₹999 keep ₹999 for their two years. That's a promise.

A cheaper check first: put both prices on a one-page WhatsApp brochure and see which one gets more "come and show me" replies from owners you reach through your work and family contacts.

## 5. The panel's price objections, word for word (for marketing to answer)

1. *"With around 40 technicians, ₹199 each comes to about ₹8,000 every month, double what the ₹99 job apps charge. I might let them run the free month, but I won't pay double just because the report is voice instead of typed."* (P011, panel v1)
2. *"For 8 boys that is about 1,600 rupees every month, and right now my technicians just send me a WhatsApp voice note and a photo of the old part for free. I might let them set up the free month, but I am not going to start paying a monthly bill for something I can mostly do with WhatsApp."* (P002, panel v1)
3. *"Calling them costs me nothing, and ₹2,499 every month for my size of team is real money next to WhatsApp, which is free."* (P006, re-test)

What these have in common: buyers compare the price with **free WhatsApp** and **₹99 typed apps**, not with the value. Marketing has to show what neither of those gives them:
- a checked report the customer receives, in the technician's own words, with proof of the part changed;
- evenings back for the owner;
- AMC renewals that don't lapse.

*Simulated buyers chose what to test here. Nothing in this file is proof that real owners will pay ₹1,499.*
