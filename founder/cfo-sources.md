# Where each number comes from

Checked 2026-10-19. **Fact** = a published price with a link. **Estimate** = my reasoning, not a quote; replace it with real quotes.

## Price
| Input | Value | Source |
|---|---|---|
| Small-tier price | ₹999 a shop-month, before GST | `founder/pitch.md` (the Founding Shop Plan test price) |

## Per paying shop-month (variable)
| Input | Value | Type | Source / reasoning |
|---|---|---|---|
| Technicians in a small shop | 8 | Estimate | middle of the 5–10 tier |
| Jobs per technician a day | 3 | **Estimate, the most important unknown** | no public source; ask real owners. 4 a day breaks the model (see the CFO note) |
| Working days a month | 26 | Estimate | six-day weeks |
| Reports a month | 624 | Derived | 8 × 3 × 26 |
| Audio per report | 1 minute | Estimate | a short spoken summary |
| Speech-to-text | ₹30 an hour = ₹0.50 a minute | Fact | [Sarvam AI pricing](https://docs.sarvam.ai/api-reference-docs/pricing), billed per second. Tamil accuracy is not tested; no language-specific rate listed ([summary](https://smallest.ai/blog/sarvam-ai-speech-to-text-pricing)) |
| AI structuring a report | ₹0.024 (was a ₹0.25 estimate) | Fact (price) + estimate (tokens) | [Sarvam pricing](https://docs.sarvam.ai/api-reference-docs/pricing): Sarvam 105B ₹15 per 1M input tokens, ₹60 per 1M output. Assumes about 1,000 input and 150 output tokens per report. Tamil quality not tested |
| WhatsApp utility message (Meta, India) | ₹0.115, plus 18% GST | Fact (third-party summaries, mostly in agreement) | [baat.ai](https://baat.ai/blog/whatsapp-api-pricing-india), [chatmaxima](https://chatmaxima.com/whatsapp-api-pricing/india/), [hyperleap](https://hyperleap.ai/whatsapp-pricing-calculator-india). One source reports a change to free-window rules from 1 Oct 2026; check [Meta's rate card](https://developers.facebook.com/docs/whatsapp/pricing) |
| WhatsApp through a reseller | ₹0.50 | Fact (one vendor) | [RichAutomate](https://richautomate.in/blog/best-whatsapp-business-api-for-ac-appliance-repair-india-2026). Used only as a what-if |
| AMC reminders a month | 20 | Estimate | |
| Payment gateway | 2% + 18% GST on the fee | Fact (Razorpay's own blog) | [Razorpay](https://razorpay.com/blog/payment-gateway-pricing-by-business-category-india/). A 90-day 0% offer exists for new merchants (same source) |

## Fixed monthly (all estimates; get quotes)
| Input | Value | Reasoning |
|---|---|---|
| Hosting, database, photo storage | ₹1,250 (was a ₹2,500 estimate) | [AWS Lightsail](https://aws.amazon.com/lightsail/pricing/): 2 GB instance US$12 a month (Mumbai gets half the transfer allowance) + about US$2 for snapshots, at an **assumed ₹88 per US$**, before GST. The managed database (US$15) is skipped, with Postgres on the same server and daily snapshots |
| Accountant for GST filing | ₹1,500 | a typical small-firm retainer in a metro. Get a quote |
| Travel for setups and support | ₹1,000 | two-wheeler or auto trips across Chennai |
| Support phone and data | ₹400 | a prepaid plan |
| Domain and email | ₹300 | |
| Founder salary | ₹0 | the founder keeps the day job. This is a real cost the model does not show |

## Startup (all estimates except the derived trial line)
| Input | Value | Reasoning |
|---|---|---|
| Android test phone | ₹12,000 | a mid-range phone typical of technicians' phones |
| Business and GST registration | ₹10,000 | CA fees. Get a quote |
| Lawyer review of privacy promise and terms | ₹10,000 | DPDP Act wording for customer data |
| Free trial months | ₹8,822 | 22 trials × ₹401 (variable cost without the gateway fee). 22 = trials needed for 11 paying shops if half pass |
| Trademark application | ₹4,500 | check the current fee on IP India |
| Speech and AI testing while building | ₹3,000 | |
| Leaflets and visiting cards | ₹3,000 | |

## Volume (ramp)
| Input | Value | Reasoning |
|---|---|---|
| Paying shops by month | 0, 1, 2 … 11 | One new paying shop a month. The panel re-test had 14 of 20 say they'd *try* it, but nearly all said they might not pay after the trial, so I assumed **half of trials pass** the 7-in-10 guarantee, and that a part-time founder can do about 2 setups a month. Month 1 is all trials, so nobody pays yet |
| Capacity | 20 paying shops | Estimate: what one part-time founder can support |
