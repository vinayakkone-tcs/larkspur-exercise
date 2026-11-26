# Client review: Larkspur disruption-care agent

**To:** Room 4  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-26 12:14

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. agent.py run_agent(): the loop now appends response.content and ends with text_of(response), a fix to what the shipped template did.**

The diff replaces messages.append({"role": "assistant", "content": text_of(response)}) with response.content, and moves answer = text_of(response) to after the while loop. The last committed run in readout-trace.json shows 4 API turns and 4 tool calls ending on cause_in_plain_words, so the loop did continue past the first tool_use. That run is a single booking.

Run python3 run.py --all --trace and paste the totals footer.

**2. agent.py system_blocks() puts cache_control on SYSTEM_PROMPT + TONE_ADDENDUM and the runtime_preamble() clock line after it.**

readout-trace.json records 20552 tokens read from cache, 2831 written, hit ratio 0.8737723736235704, from one run. The second messages.create call in the loop also passes cache_control={"type": "ephemeral"} at top level, a second marker alongside the one in system_blocks(). Nothing in the repo compares this against the uncached template on cost per conversation.

Run python3 bench.py --label before --stage 1 --runs 3 on the shipped behaviour, then again as after, and paste the python3 bench.py --compare before after output.

**3. agent.py EXTRA_TOOLS holds 5 added schemas on top of the 9 in build_tools(), and tool_list() also appends mcp_client.tools().**

The added tools are cause_in_plain_words, departures_in_window, reopen_stats, care_entitlements and seats_left. Of those, care_entitlements overlaps what check_policy already returns (meal, hotel, ground care, goodwill eligibility), and seats_left overlaps the seats left that search_alternatives already returns. Every extra schema is sent on every turn, and the static scan lists LOCAL_TOOLS executors as "?" for two entries, so I cannot see which names those two register under.

Run python3 run.py --tool-tax and python3 run.py --show-tools, and paste both outputs.

**4. agent.py TONE_ADDENDUM is still 0 characters, and the hard gate tone-0101 in evals/cases.json depends on tone.**

tone-0101 is an abuse plus legal threat case that must call escalate_to_human, and its judge grader reads the wording. The scan shows nothing in the agent beyond SYSTEM_PROMPT shaping that wording. Priya's question about a bigger model has no tone evidence behind it yet, because no run in the repo exercises the abuse case.

Run python3 eval_harness.py and paste the per-case result for tone-0101.

**5. evals/cases.json has 6 cases, and 5 of them still carry "author": "<your name>".**

Only team-0101 has a real author, Vinayak Kone. The other five are the given examples, and the _readme says the same author on every case is one person's judgement. The three hard gates (tone-0101, grnd-0101, irrv-0101) are all placeholders. The banked gates in readout.html are 1.2, 1.3, 1.4 and 4.1, and none of the eval gates (3.1 among them) are banked.

Run python3 verify.py 3.1 and paste the output.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (252 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- `evals/cases.json`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
