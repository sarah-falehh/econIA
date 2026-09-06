# EcoLingua-TN v4.30 — Final Stabilization

## Structural fixes
- Country headings are now forward context boundaries: the next section inherits the new country without contaminating the previous event.
- Local temporal scope is clause-aware: a quarter/month attached to a later value no longer propagates to earlier indicators in a multi-indicator sentence.
- Monetary `increased by X ... passing from A to B` constructions now keep A and B as levels and exclude X as a false level.
- Existing annex exclusion, conflict handling, contextual/temporal resolution, dynamic country/currency recognition, series safety and analyst exports are preserved.

## Verification
- Full automated regression suite: 144 passed, 0 failed.
- Dedicated regression tests added for all three structural defects above.
- Direct checks confirm:
  - Thailand heading -> Thailand context.
  - Portugal 1.9% growth and 2.6% inflation remain annual; 6.4% unemployment is Q4.
  - Thailand reserves yield 237.4bn (2024-M12) and 241.1bn (2025-M03); 3.7bn is not emitted as a reserve level.
