# Operations: running Sollu alongside a day job

Written 2026-10-20 from `idea.md`, `offer.md`, `pricing.md`, `marketing.md` and `numbers.json`. Here "Sollu" is the product formerly called AITechnician (see `brand.md`).

**The constraint behind everything here:** one founder with a full-time day job. Shops work 9 to 7 and call in the daytime, when you can't answer. So the software has to run the day without you, and you run the evenings and weekends.

## 1. The daily cycle

👁 = the shop or its customer sees this step.

| When | Step | Who |
|---|---|---|
| 6:30–7:30 am | Check the overnight dashboard: failed transcriptions, reports stuck unsent, server alerts. Reply to messages from the night before | founder |
| 9 am onwards | 👁 Technicians press record after each job and speak (Tamil, English or both). The audio uploads, or waits on the phone until there's signal | technician → system |
| within ~1 min | Speech-to-text (Sarvam), then structuring into problem / work done / parts / time (Sarvam 105B, or rules) | system |
| | 👁 The technician or owner sees the draft and taps **OK** or edits it | technician / owner |
| | 👁 The report (shop name first, photo of the old part) goes to the customer on WhatsApp | system |
| 10 am | 👁 AMC renewal reminders due that day go out | system |
| all day | 👁 The owner's screen shows today's jobs, reports sent and reports waiting | system |
| lunch break | Check the support WhatsApp and answer anything urgent | founder |
| 7–9 pm | Fix flagged transcriptions and add new Tamil or part words to the vocabulary list. Answer support. Call one trial shop. Check each trial shop's usage % | founder |
| 9 pm | Automatic database snapshot; check that it succeeded | system / founder |

**Weekly:**
- **Saturday:** setups and demos at shops.
- **Sunday:** dealer visits, the weekly review (section 4, SOP 5) and deploying the vocabulary update.

## 2. Suppliers

Each one maps to a cost line in `numbers.json`.

| Input | Main supplier | Published price | Alternatives | Terms / lead time | Open question |
|---|---|---|---|---|---|
| **Speech-to-text (Tamil)** | [Sarvam AI](https://docs.sarvam.ai/api-reference-docs/pricing) | **₹30 an hour**, billed per second; ₹100 free credit for new users | [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text/pricing) (US$0.016 a minute for standard V2, about 3× Sarvam; Tamil support not confirmed in what I read); open-source Indic models self-hosted (needs a GPU, so not yet) | prepaid credits, self-serve, same day | **Tamil accuracy on noisy rooftops is untested.** Test on your own recordings and on the public [Kathbath noisy Tamil test set](https://aikosh.indiaai.gov.in/home/datasets/details/noisy_tamil_asr_benchmark_dataset_kathbath_tamil_noisy_test_known.html) before promising anything. Confirm Tamil is supported in Sarvam's docs |
| **Report structuring** | [Sarvam 105B](https://docs.sarvam.ai/api-reference-docs/pricing) | **₹15 per 1M input tokens, ₹60 per 1M output** → about ₹0.024 a report (assuming ~1,000 tokens in, 150 out) | the prototype's rule-based extraction (₹0); other models on the same page (Gemma 4 31B ₹35 / ₹90) | same account as speech-to-text | quality on Tanglish transcripts; whether the rules alone are good enough |
| **WhatsApp sending** | Meta WhatsApp Cloud API, directly | **about ₹0.115** per utility message ([summaries](https://baat.ai/blog/whatsapp-api-pricing-india); [Meta rate card](https://developers.facebook.com/docs/whatsapp/pricing)) + 18% GST | resellers (Gupshup, Interakt, AiSensy, RichAutomate) are easier to set up but cost more; one charges [₹0.50 all-in](https://richautomate.in/blog/best-whatsapp-business-api-for-ac-appliance-repair-india-2026) | needs **Meta business verification** (about 3–5 business days for a proprietorship per [one guide](https://hyperleap.ai/blog/whatsapp-business-api-setup-guide-india)), **a dedicated phone number** not already on WhatsApp, and **approved message templates** | a reported rule change from 1 Oct 2026; check Meta's page. Template approval for reports with photos |
| **Hosting** | [AWS Lightsail](https://aws.amazon.com/lightsail/pricing/), Mumbai | **US$12 a month** for 2 GB / 60 GB, + about US$2 for snapshots (Mumbai gets half the transfer allowance). Managed database US$15 extra, skipped for now | DigitalOcean (Bangalore region; price not checked) | card billing, instant | the ₹88-per-US$ rate is an assumption; GST on AWS India invoices |
| **Payments** | Razorpay (subscriptions / UPI AutoPay) | **2% + 18% GST on the fee** ([Razorpay](https://razorpay.com/blog/payment-gateway-pricing-by-business-category-india/)); 90-day 0% offer for new merchants | Cashfree, or bank transfer / UPI with a monthly invoice (₹0, but manual) | KYC needs PAN, a bank account and a business proof | with under 10 shops, monthly UPI with a reminder may be simpler than a gateway |
| **Test phone** | any mid-range Android (estimate ₹12,000) | — | borrow technicians' phones during setup | buy once | which phones technicians actually carry; check at the first 3 shops |
| **Brochures** | a local print shop | estimate ₹3,000 for 100 + 20 cards | online printers | 2–3 days | get a quote |

**Changes made to `numbers.json` from these prices** (re-run 2026-10-20):
- AI structuring: ₹156 → **₹15** a shop-month.
- Hosting: ₹2,500 → **₹1,250** a month.
- Trial month: ₹542 → **₹401** a shop.

**New result: contribution ₹1,063 (71%), break-even at 5 paying shops, year 1 operating profit +₹16,758, cash needed about ₹62,942.** These numbers rest on Sarvam's prices and assume its Tamil quality is good enough, which is untested. Run `/founder-cfo` again to rewrite the CFO's note around the new figures.

## 3. People

**Nobody is paid wages in year 1.** You do everything. What has to change is when you do it.

**Founder hours, slow first month (trials, 2–3 shops):**

| Day | Hours | What |
|---|---|---|
| Mon–Fri | 1 h morning + 2 h evening = 15 h | checks, support, fixes, building features |
| Saturday | 6 h | 1 setup (half a day) + 1–2 demos |
| Sunday | 4 h | dealer visits, weekly review, deploy |
| **Total** | **about 25 h a week** on top of the day job | |

**At the plan's volume (11 paying shops, about month 12):**

| Task | Hours a week |
|---|---|
| Support: about 30 min per shop | ~5.5 |
| Fixing transcriptions and the vocabulary | ~3 |
| Setups (about 2 a month at half a day each) | ~2 |
| Demos and dealers | ~3 |
| Morning and evening checks | ~7 |
| Building and fixing | ~5 |
| **Total** | **about 25 h a week** |

That is close to the limit for one person with a day job. **At about 15 shops, plan for a part-time Tamil-speaking support helper** (evenings and Saturdays). There's no wage figure yet: ask what local part-time support staff earn before hiring, and add it to `numbers.json`. Payroll obligations (PF, ESI, professional tax) depend on headcount and structure, so check them with your CA.

**Who covers when you can't:** in a week when you're ill or traveling, nobody does. So:
- the system must run without you (section 5);
- shops must know the support promise in writing: replies within 2 hours on working days, evenings guaranteed;
- a trusted friend or family member should have read access to the status page and be able to send one "we're on it" message.

## 4. Routines (one page each)

### SOP 1: setting up a founding shop (Saturday, about 3–4 hours)
1. Before you go: create the shop's account, its WhatsApp template with the shop name, and a shop-name logo placeholder.
2. Meet the owner. Agree on which technicians start; all of them is best. Write down their phone models.
3. Install the app on each technician's phone. Each one records one test job **on a real job or the rooftop outside**, in their own words. This is the live demo the panel asked for.
4. Show the owner the draft, the **OK** tap and the WhatsApp the customer receives. Send one test report to the owner's own phone.
5. Load the AMC list from their notebook or Excel. Don't leave without this; it's the second reason they pay.
6. Explain the guarantee with the date on paper: "From [date] to [date], at least 7 in 10 jobs through the app, or you pay nothing."
7. Hand over the written privacy promise and show the Excel export button.
8. Give them your number and the support hours. Add the owner to a one-to-one WhatsApp chat (not a group).
9. That evening: check that every technician's test report arrived. Message the owner a one-line summary.

### SOP 2: the morning check (15 minutes, before the day job)
1. Open the dashboard and look at three things: failed transcriptions, reports stuck unsent, server or WhatsApp errors.
2. For any stuck report, resend it or message the owner: "Two reports from yesterday are delayed; I'll fix them by tonight."
3. Reply to all night messages, even with "seen, fixing tonight".
4. Check that last night's snapshot succeeded.

### SOP 3: complaints, starting with "it got the Tamil wrong"
1. Reply the same day, signed with your name, in the voice from `brand.md` ("Sorry, that one's on us…").
2. Get the audio and the draft. Note the wrong word or words.
3. If a wrong report **reached a customer**: offer to send a corrected report with the shop's approval, and say what happened in one line.
4. Add the word to the vocabulary or correction list that evening. Note the fix and the shop in the issue log.
5. If the same kind of error happens 3 times in a week: stop new setups until it's fixed.
6. Any complaint about **data or privacy**: answer within the hour, in writing, and follow the breach steps in section 6.

### SOP 4: day 30, the guarantee and billing
1. Two days before day 30, send the owner the usage figure: "X of Y jobs through Sollu in the last two weeks."
2. On day 30, if it's at least 70%: send the Razorpay / UPI subscription link with the founding price and the two-year lock, in writing.
3. If it's under 70%: **no bill.** Thank them, ask why in one question, and offer to stop or to try two more weeks free.
4. Record the result for the "trials that become paying shops" number in `marketing.md`.

### SOP 5: weekly review and "reorder" (Sunday, 45 minutes)
1. **Top up credits:** Sarvam balance (aim for at least 2 weeks of use), the WhatsApp payment method, AWS billing alert.
2. Ship the vocabulary update. Write down what changed.
3. Look at the three numbers from `marketing.md` (demos, usage at day 14, trial → paid) and decide one change.
4. Restore last week's snapshot to a test server once a month, to prove backups work.
5. Check every shop's usage. Phone any shop that has dropped below 60%.

### SOP 6: when the server or WhatsApp goes down
1. The technician's app keeps recordings on the phone and retries.
2. Send one WhatsApp to every affected owner: "Reports are delayed; nothing is lost; they'll send when we're back."
3. Fix it, or restore from the last snapshot. After restoring, check that no report was sent twice.
4. Afterwards, tell the shops what happened and what changed.

## 5. Tools

The smallest set that runs the business:

| Job | Tool | Price | Why |
|---|---|---|---|
| App and server | AWS Lightsail Mumbai (Postgres on the same server) | US$12 + about US$2 a month | in India (low latency, keeps data in the country), one bill, snapshots |
| Speech and structuring | Sarvam AI | ₹30 an hour for speech; ₹15 / ₹60 per 1M tokens | Indian languages are their focus; one account |
| Sending reports | Meta WhatsApp Cloud API | about ₹0.115 a message | the cheapest route; you own the number |
| Payments | Razorpay subscriptions, or a manual UPI invoice while there are under 10 shops | 2% + GST, or ₹0 | UPI AutoPay suits Indian small businesses |
| Bookkeeping | your CA, using a simple sheet of invoices and costs; a bookkeeping app later | in the ₹1,500 a month CA line | under 15 invoices a month doesn't justify software |
| Code and issues | the existing git repository | ₹0 | already in use |
| Uptime alerts | a free uptime monitor, or a Lightsail alarm | ₹0 (check the free tier) | you'll be at the day job when it fails |

The existing prototype (FastAPI, PostgreSQL, React) is the base, but **three things must be built before the first setup:**
- Tamil speech through Sarvam (the prototype uses the browser's English speech recognition);
- WhatsApp sending with one-tap approval;
- AMC reminders.

The customer web portal from the prototype is **not** part of the first offer. Hide it.

## 6. Licences, registrations and insurance (India, Tamil Nadu)

Rules differ by place and change. **Confirm each one with the authority or your CA. This is not legal advice.**

- [ ] **Your day-job contract.** Read the moonlighting, conflict-of-interest and **IP ownership** clauses before you sell anything. Some employers claim code written by employees. **This is the biggest legal risk in the plan.** Ask HR or a lawyer, and keep Sollu work off employer devices and hours.
- [ ] **Business form.** Sole proprietorship (no separate registration; PAN and bank account), or LLP / one-person company (more cost, limited liability). Decide with your CA. Budgeted at ₹10,000.
- [ ] **Udyam (MSME) registration.** Free, online at [udyamregistration.gov.in](https://udyamregistration.gov.in). It's also accepted for Meta business verification when you don't have GST ([guide](https://www.zoko.io/post/whatsapp-business-api-no-gst-number)).
- [ ] **GST.** Registration is required once services turnover passes the threshold (₹20 lakh in most states, per the [GST portal](https://www.gst.gov.in)). Year 1 revenue is about ₹99,000, so it's optional. Larger shops may prefer GST invoices so they can claim the credit. Decide with your CA.
- [ ] **Tamil Nadu Shops and Establishments.** Since the 2024 amendment, registration is online. Sources disagree on whether an establishment with **under 10 workers** needs a certificate or only has to file details ([Khaitan & Co](https://khaitanco.com/thought-leadership/Tamil-Nadu-Implements-Shops-and-Establishments-Registration-Requirement-for-Employers), [incorpx](https://www.incorpx.io/blog/shop-establishment-license-guide-india)). Check on the Tamil Nadu Labour Department portal.
- [ ] **Professional tax** (Greater Chennai Corporation): check whether it applies to your structure.
- [ ] **Data protection: the Digital Personal Data Protection Act, 2023** and its Rules. You process shops' customers' names, phone numbers and addresses on the shops' behalf. You need:
  - a written privacy promise and terms (budgeted ₹10,000);
  - a breach response plan;
  - deletion on exit.

  Check the current rules and timelines on [MeitY's site](https://www.meity.gov.in).
- [ ] **Trademark** for "Sollu" in classes 9, 42 and 38 ([IP India](https://tmrsearch.ipindia.gov.in/tmrpublicsearch/)). Budgeted ₹4,500.
- [ ] **WhatsApp Business Policy.** Templates must follow Meta's rules, and customers must have agreed to receive messages. The shop collects that agreement, so put it in the terms.
- [ ] **Income tax.** Business income goes on your personal return. Ask your CA whether the presumptive scheme suits you.
- [ ] **Insurance (optional at this size):** cyber or professional-indemnity cover once you pass about 10 shops. Get a quote; not budgeted.

## 7. Risk register

Likelihood and impact: L = low, M = medium, H = high.

| # | Risk | Likely | Impact | Plan |
|---|---|---|---|---|
| 1 | **Your employer objects, or claims the code** | M | H | read the contract now; work only on your own devices and time; get HR's answer in writing before the first paid shop |
| 2 | **Tamil speech-to-text isn't accurate enough on noisy rooftops** | H | H | test on 50 real recordings and the Kathbath noisy set **before** setting a launch date; the one-tap approval means no wrong report reaches a customer; if accuracy is poor, delay rather than launch |
| 3 | **Technicians stop recording after week 1** | H | H | the guarantee measures it; use the day-14 check (SOP 5); visit; make recording faster (one button, under 30 seconds) |
| 4 | **A shop needs you during your working hours** | H | M | support promise in writing (2 hours on working days); the system runs on its own; a trusted helper can send a status message |
| 5 | **Server outage, or reports stuck** | M | H | offline queue on the phone; daily snapshots and a monthly restore test; uptime alerts; SOP 6 |
| 6 | **WhatsApp number restricted or templates rejected** | M | H | follow Meta's policy; use utility templates only; collect customer agreement through the shop; keep SMS or the owner's own WhatsApp forward as a fallback |
| 7 | **A data leak of shops' customer lists** | L | H | data on an Indian server, backups encrypted, staff logins limited, the written privacy promise; a breach plan (tell the shops within 24 hours, then follow DPDP rules) |
| 8 | **API prices change** (Meta's reported Oct 2026 rule change; Sarvam prices) | M | M | each 1 paisa a report is about ₹6 a shop; check rates each quarter; the CFO what-ifs show the margin can absorb it |
| 9 | **Fieldproxy or TeamShastra adds Tamil voice reports** | M | M | win on local setup, the Chennai vocabulary and the guarantee; get to 10 referenceable shops quickly |
| 10 | **You burn out or fall ill** (25 hours a week on top of a job) | M | H | cap at 10 founding shops until a helper is hired; **no setups in April–June**; one day a week off |

## Open questions (only quotes or tests will answer these)

- Sarvam's **Tamil accuracy** and the minutes per report on real jobs.
- **Jobs per technician per day** at real shops. This is still the biggest number in the model.
- The **WhatsApp template** format for a report with a photo, and how long approval takes.
- **CA quotes** for registration and monthly filing.
- What your **employment contract** says about outside work and IP.
- What a part-time support helper in Chennai costs.
