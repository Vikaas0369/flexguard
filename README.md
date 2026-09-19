# FlexGuard

FlexGuard is an independent reliability-assurance prototype for offline field applications.

It combines a small reference field-inspection application with a failure-injection and validation framework that tests how important data behaves under unreliable connectivity, retries, server failures, and evidence-upload problems.

The project contains two main components:

- **FieldSync**, a reference field-inspection application used as the system under test
- **FlexGuard**, a reliability-assurance framework that injects failures, validates recovery and data integrity, records test results, and produces a release decision

> **Independent project:** FlexGuard is not affiliated with FlexManager. It does not access, test, reverse engineer, or make reliability claims about FlexManager software.

---

## Why FlexGuard

Field applications often operate outside reliable office networks.

A normal HTTP 200 response does not prove that an application will behave safely when:

- connectivity disappears
- a server processes a request but the acknowledgement is lost
- an offline record must synchronize later
- an evidence upload fails
- the client retries the same operation
- records disappear or are duplicated
- stored values change unexpectedly
- attachments are missing or corrupted
- the backend becomes slow or unavailable

FlexGuard was built to explore these failure modes systematically.

The project focuses on a simple question:

> **When something goes wrong between the field application and the server, does important inspection data remain recoverable, consistent, and safe?**

---

## Architecture

```text
                       FIELD USER
                           |
                           v
                 +-------------------+
                 |   FieldSync UI    |
                 |      :7861        |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |   Chaos Proxy     |
                 |      :9000        |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |   FieldSync API   |
                 | FastAPI + SQLite  |
                 |      :8000        |
                 +---------+---------+
                           |
                           v
                     Server State


                 FLEXGUARD ENGINE
                           |
              +------------+------------+
              |                         |
              v                         v
      Scenario Controller        Integrity Checks
              |                         |
              +------------+------------+
                           |
                           v
                   Risk / Outcomes
                           |
                           v
                   Release Decision
                           |
                           v
                    GitHub Actions
```

FieldSync now sends its API traffic through the FlexGuard Chaos Proxy.

This allows FlexGuard to change network behavior while the real reference application workflow continues to use the normal API endpoints.

---

## FieldSync

FieldSync is the purpose-built reference application used to demonstrate FlexGuard.

It allows a user to:

- create an inspection
- enter inspector information
- record findings
- add notes
- assign a risk level
- attach image evidence
- submit an inspection
- view synchronization status

### FieldSync capabilities

| Capability | Purpose |
|---|---|
| Inspection creation | Capture field inspection information |
| Evidence upload | Attach image evidence |
| Submission | Submit completed inspection records |
| Offline queue | Preserve records when the backend path is unavailable |
| Retry | Synchronize queued records after connectivity is restored |
| Idempotency | Prevent duplicate business records during retries |
| Sync status | Track pending, synced, and failed records |

FieldSync uses a persistent local SQLite queue for offline records.

A queued inspection retains the same idempotency key when retried so that uncertain network outcomes do not automatically create duplicate records.

---

# FlexGuard Test Model

FlexGuard currently runs **13 checks**.

They are deliberately separated into two categories:

```text
4 Application Resilience Scenarios
+
9 FlexGuard Detector Checks
=
13 Total Checks
```

This distinction is important.

A detector passing means FlexGuard successfully detected an intentionally injected fault.

A resilience scenario passing means the reference application actually preserved or recovered the business operation safely.

---

## Application Resilience

These are the most important FlexGuard scenarios.

They test real end-to-end behavior rather than simply confirming that an HTTP error can be detected.

| Scenario | What FlexGuard proves |
|---|---|
| Normal Request | Inspection creation and retrieval work normally |
| Offline Recovery | An inspection survives temporary connectivity failure, remains locally queued, later synchronizes, uploads evidence, submits successfully, and creates exactly one server record |
| Lost Acknowledgement | The server commits an inspection, the success response is deliberately lost, the client retries the same operation, and idempotency prevents a duplicate |
| Evidence Upload Recovery | An evidence upload fails, connectivity is restored, the evidence is retried, its checksum is verified, and the inspection is submitted successfully |

### Offline Recovery

FlexGuard validates this flow:

```text
Network/API path unavailable
        |
        v
Inspection cannot reach server
        |
        v
Saved to local queue
Status = PENDING
        |
        v
Connectivity restored
        |
        v
Same queued operation retried
        |
        v
Evidence uploaded
        |
        v
Inspection submitted
        |
        v
Local queue = SYNCED
        |
        v
Exactly one server record exists
```

### Lost Acknowledgement

This scenario reproduces an important distributed-systems uncertainty:

```text
Client sends create request
        |
        v
Server commits inspection
        |
        v
FlexGuard hides successful response
        |
        v
Client cannot know whether request succeeded
        |
        v
Same operation is retried
        |
        v
Server recognizes idempotency key
        |
        v
Existing inspection returned
        |
        v
Exactly one business record exists
```

The scenario validates the **business outcome**, rather than assuming how a production platform must implement duplicate protection internally.

### Evidence Upload Recovery

FlexGuard also validates evidence recovery:

```text
Inspection created
        |
        v
Evidence upload attempted
        |
        v
Failure injected
        |
        v
Evidence not falsely recorded as uploaded
        |
        v
Connectivity restored
        |
        v
Same evidence retried
        |
        v
Server stores evidence
        |
        v
SHA-256 checksum matches
        |
        v
Inspection submitted
```

---

## FlexGuard Detector Checks

These checks verify that the FlexGuard harness can identify injected network and data-integrity conditions.

| Detector Check | Purpose |
|---|---|
| Timeout | Detect a request exceeding its allowed response time |
| HTTP 500 | Detect a server-side failure |
| Slow Response | Detect degraded response performance |
| Missing Record | Detect a deliberately removed inspection |
| Duplicate Record | Detect duplicate stored records |
| Changed Data | Detect unexpected changes to stored inspection data |
| Missing Attachment | Detect missing evidence |
| Checksum Validation | Validate evidence integrity using a file checksum |
| Failure Replay | Record retry attempts and the final failure state |

A detector result of `DETECTED` means the test harness correctly found the injected condition.

It does **not** mean that FieldSync suffered an unresolved production failure.

---

## Test Status, Type, and Outcome

FlexGuard keeps three concepts separate.

### Test Status

**PASS**

The FlexGuard check executed successfully and verified its expected condition.

**FAIL**

The check could not verify the expected behavior.

### Scenario Type

**RESILIENCE**

Tests whether FieldSync safely preserves or recovers the real business operation.

**DETECTOR**

Tests whether FlexGuard correctly identifies an injected fault or integrity problem.

### System Outcome

**SAFE**

A resilience scenario completed with the required integrity and recovery conditions satisfied.

**DETECTED**

FlexGuard successfully identified an intentionally injected fault.

**UNSAFE**

A required check failed.

Example:

```text
Scenario: Offline Recovery
Status:   PASS
Type:     RESILIENCE
Outcome:  SAFE
Risk:     Critical
```

Compared with:

```text
Scenario: HTTP 500
Status:   PASS
Type:     DETECTOR
Outcome:  DETECTED
Risk:     Medium
```

That distinction prevents a detector self-test from being presented as proof that the application itself recovered.

---

## Risk Engine

Each scenario has a risk classification:

```text
Low
Medium
High
Critical
```

FlexGuard also calculates a weighted **Test Assurance Score** across the checks.

A successful current run looks like:

```text
Total Checks:             13
Application Resilience:   4 / 4 SAFE
Detector Checks:          9 / 9 PASS
Failed Checks:            0
Test Assurance Score:     100.0%
Overall Risk:             Low
```

The percentage is a supporting test metric.

It is **not** the primary release rule.

Application resilience is evaluated separately.

---

## Release Decision

The release decision is based on the real application-resilience scenarios.

```text
Application Resilience
        |
        v
Are all required resilience scenarios SAFE?
        |
      /   \
    No     Yes
    |       |
    v       v
 BLOCK    RELEASE
RELEASE   APPROVED
```

For the current prototype:

```text
Offline Recovery UNSAFE
        ->
BLOCK RELEASE

Lost Acknowledgement UNSAFE
        ->
BLOCK RELEASE

Evidence Upload Recovery UNSAFE
        ->
BLOCK RELEASE
```

Detector checks are handled separately.

If a detector check fails, the CI pipeline also fails because the FlexGuard test harness itself cannot be considered healthy.

---

## Failure Replay

FlexGuard records retry behavior so a failure sequence can be inspected after execution.

Example:

```text
Request started
Retry attempt 1
Server returned HTTP 500
Retry required
Retry attempt 2
Server returned HTTP 500
Retry required
Retry attempt 3
Server returned HTTP 500
Maximum retries reached
Final state: FAILED
```

This provides a simple reproducible timeline instead of only reporting:

```text
Test failed
```

---

## Dashboard

The dashboard intentionally separates application behavior from test-harness validation.

### Application Resilience

Displays the four real resilience scenarios:

```text
Normal Request
Offline Recovery
Lost Acknowledgement
Evidence Upload Recovery
```

### FlexGuard Detector Checks

Displays the nine fault and integrity detector checks separately.

The dashboard summary includes:

```text
Total Checks
Application Resilience
Detector Checks
Failed Checks
Test Assurance Score
Overall Risk
Release Decision
```

A successful run currently reports:

```text
Application Resilience   4 / 4 SAFE
Detector Checks          9 / 9 PASS
Failed Checks            0
Release Decision          RELEASE APPROVED
```

---

## Screenshots

### FieldSync

FieldSync captures field inspection data, evidence, risk classification, and synchronization state.

![FieldSync inspection workflow](docs/screenshots/fieldsync.png)

### FlexGuard Dashboard

The FlexGuard dashboard separates application resilience from detector checks and produces a release decision.

![FlexGuard reliability dashboard](docs/screenshots/flexguard-dashboard.png)

### GitHub Actions

The same validation executes automatically in CI.

![FlexGuard GitHub Actions pipeline](docs/screenshots/github-actions.png)

---

# CI/CD

FlexGuard uses GitHub Actions to execute the reliability suite automatically.

The workflow runs on pushes and pull requests to the `main` branch.

```text
Checkout repository
        |
        v
Install dependencies
        |
        v
Run release-gate unit tests
        |
        v
Start FieldSync API
        |
        v
Start Chaos Proxy
        |
        v
Run FlexGuard
        |
        +--------------------------+
        |                          |
        v                          v
Application Resilience      Detector Checks
        |                          |
        +-------------+------------+
                      |
                      v
             Generate JSON Report
                      |
                      v
               Release Decision
                      |
                 +----+----+
                 |         |
                 v         v
               PASS       FAIL
```

A successful CI result looks like:

```text
FLEXGUARD CI REPORT
========================
Application Resilience: 4/4 SAFE
Detector Checks: 9/9 PASS
Test Assurance Score: 100.0%
Overall Risk: Low
Release Decision: RELEASE APPROVED

PIPELINE RESULT: PASS
```

The generated JSON report is uploaded as a GitHub Actions artifact rather than stored permanently in the repository.

---

# Running the Project

## 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## 3. Start the complete environment

```powershell
python app.py
```

One command starts the FlexGuard lab.

```text
FieldSync UI
http://127.0.0.1:7861

FlexGuard Dashboard
http://127.0.0.1:7860

Chaos Proxy
http://127.0.0.1:9000

FieldSync API
http://127.0.0.1:8000

FastAPI Documentation
http://127.0.0.1:8000/docs
```

The FieldSync and FlexGuard browser tabs open automatically.

---

# Demo Flow

## 1. Create a normal inspection

Open FieldSync and enter:

```text
Location
Inspector
Finding
Notes
Risk Level
Evidence
```

Create and submit the inspection.

The successful state should show:

```text
Status: SUBMITTED
Sync:   SYNCED
```

## 2. Explain the engineering problem

A normal submission is not the difficult case.

The important question is what happens when:

```text
connectivity disappears
a response is lost
an upload fails
a retry occurs
```

## 3. Run FlexGuard

Switch to the FlexGuard dashboard and click:

```text
RUN FLEXGUARD TEST SUITE
```

## 4. Show Application Resilience

Highlight:

```text
Offline Recovery
Lost Acknowledgement
Evidence Upload Recovery
```

These demonstrate real recovery behavior.

## 5. Show Detector Checks

Explain that FlexGuard also verifies that intentionally injected faults and data-integrity problems are detected correctly.

## 6. Show the release decision

A successful run should display:

```text
Application Resilience   4 / 4 SAFE
Detector Checks          9 / 9 PASS
Release Decision         RELEASE APPROVED
```

## 7. Show GitHub Actions

Open the latest workflow run and show that the same suite executes automatically in CI.

---

# Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| Backend API | FastAPI |
| User Interface | Gradio |
| Local / Server Storage | SQLite |
| ORM | SQLAlchemy |
| HTTP Client / Testing | HTTPX |
| Automated Tests | Pytest |
| Failure Injection | Custom FastAPI Chaos Proxy |
| CI/CD | GitHub Actions |
| Source Control | Git and GitHub |

---

# Project Structure

```text
FlexGuard/
|
|-- app.py
|
|-- fieldsync/
|   |-- main.py
|   |-- database.py
|   |-- models.py
|   |-- frontend.py
|   `-- offline_queue.py
|
|-- guard_engine/
|   |-- runner.py
|   |-- replay.py
|   |-- risk_engine.py
|   |-- dashboard.py
|   |-- ci_runner.py
|   |
|   |-- chaos/
|   |   `-- proxy.py
|   |
|   `-- scenarios/
|       |-- normal_request.py
|       |-- offline_recovery.py
|       |-- lost_acknowledgement.py
|       |-- interrupted_upload.py
|       |-- timeout_request.py
|       |-- http_500.py
|       |-- slow_response.py
|       |-- missing_record.py
|       |-- duplicate_record.py
|       |-- changed_data.py
|       |-- missing_attachment.py
|       |-- checksum_validation.py
|       `-- failure_replay.py
|
|-- tests/
|   `-- test_release_gate.py
|
|-- docs/
|   `-- screenshots/
|
|-- reports/
|-- uploads/
|
|-- requirements.txt
|-- .gitignore
|-- LICENSE
`-- README.md
```

`interrupted_upload.py` retains its historical filename, but the active scenario implemented inside it is **Evidence Upload Recovery**.

---

# Engineering Concepts Demonstrated

FlexGuard demonstrates practical work with:

- API development
- offline-first workflow design
- persistent retry queues
- failure injection
- chaos testing
- unreliable-network simulation
- idempotent request handling
- lost-acknowledgement recovery
- duplicate prevention
- evidence recovery
- SHA-256 integrity verification
- local/server state validation
- automated testing
- failure replay
- risk classification
- release assurance
- CI/CD release gates
- GitHub Actions
- reproducible defect scenarios
- distributed-systems failure reasoning

---

# Scope and Limitations

FlexGuard is a portfolio reliability-engineering prototype.

FieldSync is a purpose-built reference application created specifically as the system under test.

The project does **not**:

- integrate with FlexManager
- test FlexManager systems
- reverse engineer FlexManager
- claim that FlexManager has any of the simulated defects
- attempt to reproduce FlexManager's internal implementation

The simulated scenarios represent general engineering risks that can occur in offline and distributed field applications.

The Chaos Proxy and reference application are designed for demonstration and engineering validation, not production-scale network emulation or load testing.

---

# Motivation

FlexGuard was created after studying the engineering challenges involved in offline field applications.

The project explores how failure injection, recovery validation, data-integrity checks, and CI release gates can be combined to test difficult field-workflow conditions before software is released.

The objective is not to reproduce a commercial platform.

The objective is to demonstrate a practical reliability-engineering approach to a difficult class of software problems.

---

# Author

**Vikas Y**

Software & DevOps Engineer

GitHub: **Vikaas0369**