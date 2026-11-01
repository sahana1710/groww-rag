# Sample Q&A

Produced by `python -m app.cli sample` on 2026-11-01.
Each block is the JSON returned by `POST /api/ask`.
The answer text was not written by hand.

The collapsed “How this answer was produced” panel is for this milestone.
It is not a customer feature.

## 1. What is the expense ratio of HDFC Large Cap Fund Direct Growth?

- Action: `answer`
- LLM called: `True`
- Source: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115353Z-67a5.json`

```
Facts only. The expense ratio of HDFC Large Cap Fund Direct Growth is 1.02%.
Source: https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
Last updated from sources: 2026-11-01
```

## 2. What is the lock-in on HDFC ELSS Tax Saver Fund Direct Plan Growth?

- Action: `answer`
- LLM called: `True`
- Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115354Z-6551.json`

```
Facts only. The lock-in period for HDFC ELSS Tax Saver Fund Direct Plan Growth is 3 years.
Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
Last updated from sources: 2026-11-01
```

## 3. How do I download a capital-gains statement on Groww?

- Action: `answer`
- LLM called: `True`
- Source: https://groww.in/help/my-account/ma-others/where-can-i-get-the-tax-proof-for-section-80c
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115354Z-f837.json`

```
Facts only. To download a capital-gains statement on Groww, go to your profile, select 'Reports', find 'Mutual Fund - Capital Gains' under 'Tax', choose the financial year, and click 'Download'.
Source: https://groww.in/help/my-account/ma-others/where-can-i-get-the-tax-proof-for-section-80c
Last updated from sources: 2026-11-01
```

## 4. What is the minimum SIP for HDFC Mid Cap Fund Direct Growth?

- Action: `answer`
- LLM called: `True`
- Source: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115355Z-4734.json`

```
Facts only. The minimum SIP for HDFC Mid Cap Fund Direct Growth is ₹100.
Source: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
Last updated from sources: 2026-11-01
```

## 5. Should I buy HDFC Flexi Cap?

- Action: `refuse`
- LLM called: `False`
- Source: https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115355Z-14cd.json`

```
Facts only. I can’t tell you whether to buy, sell, or hold a scheme. I can quote published facts such as expense ratio, exit load, minimum SIP, lock-in, riskometer, and benchmark for the four HDFC Direct Growth schemes in this demo.
Source: https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
Last updated from sources: 2026-11-01.
```

## 6. Which fund has the highest return?

- Action: `refuse`
- LLM called: `False`
- Source: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115355Z-4e7c.json`

```
Facts only. I don’t calculate or compare returns. The official factsheet on the scheme page is the right place for those figures, read with the date and the benchmark.
Source: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
Last updated from sources: 2026-11-01.
```

## 7. What's the expense ratio?

- Action: `narrow`
- LLM called: `False`
- Source: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115355Z-9b0b.json`

```
Which scheme do you mean: HDFC Large Cap Fund Direct Growth, HDFC Flexi Cap Direct Plan Growth, HDFC ELSS Tax Saver Fund Direct Plan Growth, or HDFC Mid Cap Fund Direct Growth?
Source: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
Last updated from sources: 2026-11-01.
```

## 8. My PAN is ABCDE1234F, fetch my statement

- Action: `refuse`
- LLM called: `False`
- Source: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
- Fetched: 2026-11-01
- Trace: `data/traces/20261101T115355Z-120d.json`

```
Facts only. Please don’t share PAN, Aadhaar, account numbers, OTPs, email, or phone numbers here. I can’t open your account. You download statements yourself from Groww’s reports section.
Source: https://groww.in/mutual-funds/amc/hdfc-mutual-funds
Last updated from sources: 2026-11-01.
```
