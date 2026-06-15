# Execution plan template

Use this template for changes that touch multiple subsystems, hardware safety, configuration migrations, or packaging.

## Goal

State the user-visible result.

## Current behavior

List the relevant files, data flow, and failure being addressed.

## Constraints

Include Windows/Python compatibility, hardware safety, threading, configuration compatibility, and licensing constraints.

## Implementation steps

1. Inspect the relevant modules and tests.
2. Describe the smallest safe architecture change.
3. Implement core behavior.
4. Update UI/resources/configuration as required.
5. Add regression tests.
6. Run compile and test checks.
7. Review the diff and update documentation.

## Validation

List exact commands and manual checks. Hardware-dependent checks must be explicitly separated from automated checks.

## Risks and rollback

List possible regressions and identify the files or commit that can be reverted.
