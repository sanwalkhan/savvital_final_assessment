# Task 2 — Dashboard Write-Up

**Dataset:** Customer Support Ticket Dataset (Kaggle · suraj520, 8,469 tickets)

## Why These Metrics
I selected these metrics to answer the key operational questions a support leader would need at a glance: workload balance, resolution effectiveness, service quality, and channel demand. Ticket status distribution shows where tickets are stuck. Resolution rate over time reveals whether the team is keeping pace with demand. Average resolution time by ticket type highlights process or staffing issues across problem categories. Customer satisfaction trend checks whether service speed and quality are actually improving. Channel share identifies where customers are arriving so resource investments can be focused.

## What the Data Says
The story here is one of mixed performance. Strong resolution rates do not always coincide with high satisfaction, suggesting many tickets are closed without fully resolving the customer’s issue. Technical tickets are the slowest to resolve, while refund requests are also slower than expected—indicating a procedural drag rather than just complexity. Email dominates the volume, so improving email triage would likely yield the biggest overall impact.

## One Dataset Limitation
The dataset does not include a true ticket open date or first response timestamp. That means average resolution time is anchored to purchase date or ticket creation date rather than the moment the customer entered the queue. As a result, the metric may reflect customer behavior more than support team efficiency. For a real operational dashboard, a separate ticket open timestamp would be essential.
