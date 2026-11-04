# Data - Take Home Task: Org Chart Inference

## Context

Imagine you're building for a **startup**. For every company in the database there is a flat list of people with job titles, but no idea who reports to whom. Sales teams keep asking: *"who runs the data team at this company?"*, *"who does the Head of Security report to?"*, *"who is the economic buyer above this champion?".* Your job is to turn that flat list into an org chart.

## The Task

Build a small **org chart inference platform**. For every company, infer who reports to whom from job titles and whatever else you can extract or derive, with a confidence on each reporting line. Where you can't resolve a manager, don't guess. A wrong edge is worse than no edge.

## Dataset

There is **no dataset**. You will generate one.

- **Minimum of 500 companies**, each with **at least 100 employees**
- A realistic mix of job titles across functions and seniority levels, with a mix of industries and company sizes
- Make it messy, like real data is: inconsistent titles, abbreviations, missing fields

How you design the data is part of the test. Think about how you'll know if your inference is right.

## How We Work

Firmable is fully **AI-native**. AI is the workflow, not a tool bolted on. We'll look at **how you build** as much as what you ship, and we're eager to see out-of-the-box ideas, in the data, in the inference, and in your dev loop.

## Deliverables

1. **A working, hosted app** where we can pick a company and see its inferred org chart. Share the link.
2. **A Git repository** with your source code, your dataset generator, and a short write-up of your approach, your key decisions, and how you measured whether it works.
3. Please share your submission within **5 days** of receiving this task.

Looking forward to seeing what you build. 🚀
