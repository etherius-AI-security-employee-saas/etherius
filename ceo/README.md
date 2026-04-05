# Etherius CEO Control

This folder is provider-only (not for customers).

## Purpose

Use the CEO console to:

1. Issue customer subscription keys with seat limits.
2. Track each customer's seat usage and online endpoint health.
3. Monitor customer login/logout activity totals per day.

Private CEO API routes:
1. `/api/ceo/health`
2. `/api/ceo/swagger` (if enabled in backend settings)

## Start

Run:

`CEO_START_CONSOLE.bat`

For signed production build (recommended), run:

`CEO_BUILD_SIGNED_RELEASE.bat`

## Required

Enter your `CEO Master Key` in the console before issuing keys or loading customers.

## Release Safety Check

Run:

`VERIFY_RELEASE_SIGNATURE.ps1`

Only distribute installer builds when signature status is `Valid`.
