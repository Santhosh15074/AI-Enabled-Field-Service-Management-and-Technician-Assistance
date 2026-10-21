# Update after ops (2026-10-20)

`/founder-ops` replaced two estimates with published prices (sources in `ops.md` and `cfo-sources.md`):
- **AI structuring falls from ₹0.25 to about ₹0.024 a report** (Sarvam 105B). That's ₹156 → ₹15 a shop.
- **Hosting falls from ₹2,500 to ₹1,250 a month** (AWS Lightsail with the database on the same server).

The trial-month cost falls to ₹401 a shop. **The re-run figures are in the table below.** The notes further down were written with the older numbers and are kept for the reasoning. Still unverified: **Tamil accuracy** of both Sarvam models on real rooftop jobs, and the **jobs per technician per day**.

# Update after pricing (2026-10-19)

`/founder-pricing` set the Starter tier at **₹1,499 a month (up to 10 technicians, 750 reports)**, and `numbers.json` now uses that price. The model below has been re-run:
- **Contribution ₹922 (62%)** per paying shop.
- **Break-even at 7 shops.**
- **Margin at plan +27%**, with the business running at a profit from about month 8.
- **Year 1 operating profit -₹7,548.**
- **Cash needed about ₹74,962.**

The note below was written at ₹999 and is kept for the reasoning; its what-ifs still hold. Cutting the paid AI call and the fixed costs on top of ₹1,499 is the "all three together" case: year 1 **+₹26,748**.

# CFO's note

**Bottom line: at ₹999 for a small shop, year 1 loses money and the business needs about ₹94,000 before it pays for itself.** That's not because the idea fails. It's because the flat price is too low for what each report costs to make. Three changes together, described below, turn year 1 into an operating profit. Most inputs are estimates (see `cfo-sources.md`). The single biggest unknown is **how many jobs a technician does a day**, and only real shop owners can tell you that.

- **The margin.** Each paying small shop (8 technicians, ₹999) leaves **₹433 (43%)** after its own costs. Tamil speech-to-text (₹312) and the AI that structures each report (₹156) eat most of it. WhatsApp itself is cheap at ₹72. Fixed costs are ₹5,700 a month, so **break-even is 14 paying shops**. The plan reaches 11 by month 12, so the margin at plan is **-9%** and year 1 operating profit is **-₹39,822**.

- **The line to watch: jobs per technician per day.** The price is flat, but every report costs speech, AI and a message. At 3 jobs a day the contribution is ₹433. At **4 jobs a day it falls to ₹252 (25%), and break-even rises to 23 shops**, more than the 20 one part-time founder can support. A busy shop on a flat price is the worst customer you can have. The price needs a fair-use limit on reports (for example, 800 reports a month for the small tier) or one more tier, and `/founder-pricing` should decide which.
  - A second risk: if WhatsApp goes through a reseller at ₹0.50 a message instead of Meta's ₹0.115, contribution drops to **₹193** and break-even to 30 shops. Use Meta's Cloud API directly.

- **Cash.** Startup spend is **₹54,424**. The largest line is ₹11,924 for about 22 free trial months: if half the trials pass the 7-in-10 guarantee, 11 paying shops need 22 trials. With the year-1 operating losses, **you need about ₹94,000 before it pays for itself**, and it doesn't earn back within year 1. Your salary isn't counted, because you keep your day job. That's the real subsidy here.

- **Three ways to improve the margin** (each run as a what-if; the scenario files are in `cfo-whatif/`):
  1. **Price the small tier at ₹1,499 instead of ₹999.** Contribution goes from ₹433 to ₹933, break-even from 14 to 7 shops, and year 1 from -₹39,822 to **-₹6,822**. The panel's middle "getting expensive" point for small shops was about ₹1,500, so this is at the edge of what they'll accept. `/founder-pricing` should test it.
  2. **Structure reports without a paid AI call** (the prototype's rule-based extraction, or a local model) once Tamil works. Contribution rises to ₹589 and break-even falls to 10. Shorter recordings (40 seconds instead of 60) add another ₹104 a shop: contribution ₹537, break-even 11.
  3. **Cut fixed costs**: hosting at ₹1,000 instead of ₹2,500, and travel at ₹500 instead of ₹1,000. Break-even falls to 9 and year 1 to -₹15,822.
  - **All three together** (₹1,499, no paid AI, lower fixed costs): contribution **₹1,078 (72%)**, break-even **4 shops**, year 1 operating profit **+₹26,748**. Cash needed is still about **₹62,756**, because the startup spend isn't earned back in year 1.

- **The board's money conditions** (`board.md`):
  - [ ] **"A price that clears hosting and support"**: **not met at ₹999** (break-even of 14 shops against a plan of 11). Met at ₹1,499 with the cost cuts.
  - [ ] **"A guarantee the business can afford"**: **met only if most trials pass.** Each failed trial costs about ₹542 plus a setup visit. At a 50% pass rate that's one extra free month per paying shop. At 30%, reaching 11 paying shops needs about 37 trials, which is more setups than you can do part-time in a year. The limit is your time, not the money.
  - [ ] **"Cost to win and support one customer"**: partly known. In money it's about ₹542 for each trial plus travel. The real cost is half a day of your time per setup, and that number needs measuring on the first shops.

GST: prices here are before 18% GST. Registration is required above the turnover threshold for services and is optional below it; business buyers can usually claim it back. **This is not financial, tax or legal advice. Have a CA check the business structure, GST and the DPDP privacy obligations before money moves.**

---

# Unit economics: AITechnician Founding Shop Plan (base case: Starter tier, up to 10 technicians, 750 reports a month)

Every number below comes from `numbers.json`; where each input came from is in `cfo-sources.md`. The tool counts in "days"; here one "day" is set to one month, so every "a month" figure is **paying shops in that month**. Amounts are rupees, before 18% GST.

## One paying shop-month (small tier, assumes 8 technicians)

| line | per paying shop-month (small tier, assumes 8 technicians) |
| --- | ---: |
| Price | ₹1,499.00 |
| Tamil speech-to-text: 624 reports x 1 min x Rs 0.50/min (Sarvam Rs 30/hour) | -₹312.00 |
| AI structuring of each report: 624 x about Rs 0.024 (Sarvam 105B, Rs 15 in / Rs 60 out per 1M tokens, ~1,000 in + ~150 out tokens) | -₹15.00 |
| WhatsApp report messages: 624 x Rs 0.115 (Meta utility rate) | -₹72.00 |
| WhatsApp AMC reminders: about 20 x Rs 0.115 | -₹2.00 |
| Payment gateway: 2% + 18% GST on the fee (Razorpay standard) | -₹35.00 |
| **Contribution** (what each paying shop-month (small tier, assumes 8 technicians) leaves to pay the fixed costs) | **₹1,063.00** (71%) |

## The margin that matters

Fixed costs: ₹4,450 a month (Hosting: AWS Lightsail 2 GB instance US₹12 + snapshots/storage ~US₹2, at ~Rs 88/US₹ (database on the same server) ₹1,250, Accountant for GST filing (estimate) ₹1,500, Travel for setup and support visits in Chennai (estimate) ₹1,000, Support phone line and data (estimate) ₹400, Domain and email (estimate) ₹300, Founder salary (day job; none taken) ₹0).

- **Break-even: 5 paying shops a month.** Below that you lose money every month.
- **Profit margin at your plan** (11 a month): **44%** of every sale, after every cost.
- Capacity: 20 a month.

## Year 1, month by month

| month | paying shop a month | revenue | profit | cumulative (after ₹51,322 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | ₹0 | -₹4,450 | -₹55,772 |
| 2 | 1 | ₹1,499 | -₹3,387 | -₹59,159 |
| 3 | 2 | ₹2,998 | -₹2,324 | -₹61,483 |
| 4 | 3 | ₹4,497 | -₹1,261 | -₹62,744 |
| 5 | 4 | ₹5,996 | -₹198 | -₹62,942 |
| 6 | 5 | ₹7,495 | ₹865 | -₹62,077 |
| 7 | 6 | ₹8,994 | ₹1,928 | -₹60,149 |
| 8 | 7 | ₹10,493 | ₹2,991 | -₹57,158 |
| 9 | 8 | ₹11,992 | ₹4,054 | -₹53,104 |
| 10 | 9 | ₹13,491 | ₹5,117 | -₹47,987 |
| 11 | 10 | ₹14,990 | ₹6,180 | -₹41,807 |
| 12 | 11 | ₹16,489 | ₹7,243 | -₹34,564 |

- **Year 1 operating profit: ₹16,758** on ₹98,934 of revenue.
- After the ₹51,322 startup spend: -₹34,564.
- Startup money earned back: not within year 1.
- Cash you need before it pays for itself: **₹62,942**.

## What if

| scenario | margin at plan | break-even a month | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 44% | 5 | ₹16,758 |
| Price -10% | 38% | 5 | ₹6,865 |
| Volume -20% | 37% | 5 | ₹2,726 |
| Unit costs +15% | 40% | 5 | ₹12,442 |

## Red flags

- The startup spend is not earned back within year 1.
