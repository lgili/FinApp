## Why
- The roadmap targets increased coverage (≥85%), performance benchmarks, golden tests, and documentation refresh before expanding scope further.
- Capturing these polish goals ensures quality debt is addressed systematically rather than ad-hoc.
- Aligning with OpenSpec clarifies acceptance metrics for testing, performance, and docs.

## What Changes
- Raise automated test coverage to ≥85% with additional unit, integration, and end-to-end suites.
- Implement golden tests for reports, benchmark large datasets (50k postings), and optimize where needed.
- Expand documentation (README, ADRs, guides) and remove legacy code remnants.

## Impact
- Touches multiple modules (tests, performance harness, docs) without introducing new features.
- Requires measurement tooling and CI updates to enforce new thresholds.
- Improves maintainability and developer onboarding experience.
