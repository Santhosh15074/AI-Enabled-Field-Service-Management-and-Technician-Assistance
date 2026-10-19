# Evaluation

How well each of the four AI components works, measured on data none of them was trained on.
Regenerate every number and chart below with:

```
python ml/evaluate.py
```

which rewrites [evaluation/results.md](evaluation/results.md) (full tables) and the charts in
`docs/evaluation/`. The script calls the same code the app serves from (the saved model files,
`suggest_fixes`, `extract_fields` and the app's risk thresholds), so the results describe the
running system rather than a separate notebook copy.

## Summary

| Component | Test data | Headline result | Baseline |
|---|---|---|---|
| Urgency classifier | 3,268 held-out support tickets | 62.2% accuracy, macro F1 0.614 | Majority class: 40.5%, F1 0.192 |
| Failure prediction | 2,000 held-out sensor readings (68 failures) | ROC-AUC 0.958; catches 75% of failures at the "critical" level, 88% at "moderate" or above | Random: PR-AUC 0.034 vs 0.774 |
| Troubleshooting assistant | 40 complaints + 8 off-topic queries | 90% top-1, 100% top-3; all 8 off-topic queries rejected | Keyword search: 77.5% top-1, 92.5% top-3 |
| Report extraction | 12 labelled technician reports | Action and time 100%, issue 91.7%, parts 100% precision / 88.9% recall | — |

## 1. Urgency classifier

**Method.** TF-IDF features (unigrams and bigrams) with logistic regression, trained on the
English rows of a public customer-support ticket dataset whose own `priority` column (low, medium,
high) matches the app's urgency levels. The held-out split is the same stratified 20%
(`random_state=42`) the training script reserves, so no test ticket was seen in training.

**Results.** 62.2% accuracy and macro F1 0.614, against 40.5% and 0.192 for always predicting the
most common class. Recall on **high** urgency, the class that matters most for queue ordering, is
65.8%.

![Urgency confusion matrix](evaluation/urgency_confusion_matrix.png)

**Discussion.** About four in five errors are between neighbouring levels (low/medium or
medium/high), the less harmful kind of mistake for ordering a queue. The costliest error, a
high-urgency ticket rated low, happened for 147 of 1,269 high tickets (11.6%). The ceiling is
set mainly by the data: priority in the source dataset was assigned by people with inconsistent
judgement, and the tickets are IT-helpdesk rather than field-service complaints, so some domain
vocabulary (pumps, compressors, breakers) is rare in training. Because of this, urgency in the app
only orders the admin's list; it never blocks or auto-assigns anything, and the admin sees the full
description.

## 2. Failure prediction

**Method.** A random forest (300 trees, balanced class weights) on the AI4I 2020
predictive-maintenance dataset's five sensor readings and quality grade. Failures are rare (3.4%),
so accuracy is meaningless here (predicting "no failure" every time scores 96.6%); the model is
judged on recall of real failures and on precision-recall area.

**Results.** ROC-AUC 0.958 and average precision 0.774, against 0.034 for a random model.

| Threshold | Recall | Precision | Readings flagged |
|---|---|---|---|
| 0.08 (app: moderate) | 88.2% | 36.6% | 8.2% |
| 0.25 (app: critical) | 75.0% | 68.9% | 3.7% |
| 0.50 (sklearn default) | 47.1% | 91.4% | 1.8% |

On the test set, the app's three levels put 51 of 68 real failures in **critical**, 9 in
**moderate** and 8 in **good**, while 1,828 of 1,932 healthy readings are rated **good**.

![ROC and precision-recall curves](evaluation/failure_roc_pr.png)
![Feature importance](evaluation/failure_feature_importance.png)

**Discussion.** The thresholds are deliberately far below the default 0.5. At 0.5 the model would
miss more than half of real failures; at the app's 0.25 it catches three in four while still being
right about two times in three when it says "critical". For maintenance this is the right trade:
a false alarm costs one inspection, a missed failure costs the equipment. Rotational speed, torque
and tool wear carry most of the signal, consistent with the dataset's documented failure modes
(power, overstrain and tool-wear failures); the quality grade contributes almost nothing.

The main limitation is that AI4I 2020 is synthetic data modelled on a milling machine. Real
equipment of other types would need its own labelled readings before these exact numbers can be
relied on.

## 3. Troubleshooting assistant

**Method.** No trained model of its own: the complaint and every knowledge-base issue are turned
into sentence embeddings with `all-MiniLM-L6-v2`, and entries are ranked by cosine similarity. Up
to three entries scoring at least 0.35 (`MIN_SIMILARITY`) are shown. There is no public dataset of
field-service complaints matched to fixes, so the test set
([troubleshooting_queries.json](../ml/eval_data/troubleshooting_queries.json)) was written by hand:
two complaints per knowledge-base entry, phrased the way a customer would and avoiding the entry's
own wording where possible, plus eight off-topic queries (billing, passwords, opening hours) that
should get no suggestion at all.

**Results.**

| Method | Top-1 | Top-3 | Mean reciprocal rank |
|---|---|---|---|
| Keyword search (TF-IDF) | 77.5% | 92.5% | 0.860 |
| Semantic search (app) | 90.0% | 100.0% | 0.950 |

With the 0.35 cut-off applied, every one of the 40 complaints got its correct fix among the
suggestions shown, and all 8 off-topic queries got none.

![Similarity distribution](evaluation/troubleshooting_similarity.png)

**Discussion.** Semantic matching beats keyword matching most clearly where a customer uses
different words from the entry: "Water is seeping out from where two pipes are joined" (keyword
search ranked the right entry 4th; semantic search 1st, "leak at a pipe joint") and "Sink water is
not draining away" (4th against 1st, "drain is clogged"). All four semantic top-1 misses still
ranked the right entry second, and each was beaten by an entry sharing the same equipment or
symptom: "The pump shakes a lot" matched "pump won't prime" first, and "Power to the machine keeps
cutting out" matched "no power even though the breaker is on" first. This is why the app shows up
to three suggestions rather than one.

The chart shows the cut-off sits in a clear gap: the closest off-topic query scores 0.21, the
weakest correct match 0.353. That correct match is only just above the cut-off, though, so raising
it would start hiding real fixes; 0.35 should be treated as an upper bound. The test set is
small and written by the developer, so these figures are optimistic; feedback from real complaints
would be needed to confirm them.

## 4. Report extraction

**Method.** Rule-based: keyword patterns pick out the diagnosis sentence, action sentences, parts
after verbs such as "replaced" or "installed", and durations in hours or minutes. There is no
dataset of field-service reports to train or test on, so 12 reports were written and labelled by
hand ([service_reports.json](../ml/eval_data/service_reports.json)). A field counts as correct if
it contains the labelled phrase; parts are scored per part.

**Results.**

| Field | Score |
|---|---|
| Issue | 91.7% (11 of 12) |
| Action taken | 100% |
| Time spent | 100%, including mixed forms such as "1 hr 15 min" |
| Parts used | 100% precision, 88.9% recall |

**Discussion.** Both misses are known limitations of a rule-based approach:

- *Issue:* "The condensate drain line was blocked." states the cause without a diagnostic marker
  ("found", "caused by", "root cause"), so the extractor fell back to the first sentence, which
  describes the symptom instead.
- *Parts:* "Replaced the belt and the bearing" yields only "belt", because coordinated parts after
  one verb aren't split (documented in `app/report_extraction.py`).

Neither causes a bad record: extraction is only a preview, and the technician reviews and corrects
every field before the report is saved. A trained extractor would need a corpus of real reports,
which the system itself will collect over time in the `service_reports` table.

## 5. Threats to validity

- **Domain mismatch.** The urgency classifier is trained on IT-helpdesk tickets and the failure
  model on synthetic milling-machine data, not on this business's own records.
- **Hand-written test sets.** The troubleshooting and extraction test sets are small and were
  written by the same person who wrote the knowledge base and the rules, which tends to inflate
  scores.
- **Single split.** Model results come from one stratified 80/20 split; the urgency and failure
  datasets are large enough that the figures are stable, but cross-validation would give
  confidence intervals.

Each of these is mitigated in the design rather than ignored: every AI output is advisory, has a
safe fallback, and is reviewed by a person before it affects a record.
