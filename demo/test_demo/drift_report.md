 # API Behavioral Drift Detection Report

 **Generated:** 2026-05-09 01:18:10 UTC
 **API:** Demo User API v1.0.0
 **Base URL:** http://localhost:8000

 ---

 ## 📊 Executive Summary

 - **Overall Drift Score:** 0.42 (MODERATE)
 - **Total Issues Found:** 8
 - **Tests Executed:** 25
 - **Tests Passed:** 15 (60.0%)
 - **Tests Failed:** 10 (40.0%)

 ### Drift Breakdown

 | Type | Score | Issues | Severity |
 |------|-------|--------|----------|
 | Contract Drift | 0.35 | 3 | 🔴 HIGH |
 | Validation Drift | 0.28 | 3 | 🟡 MEDIUM |
 | Behavioral Drift | 0.15 | 2 | 🟢 LOW |

 ---

 ## 🔥 Critical Issues

 ### Contract Drift Issues

 #### Issue #1: Missing required field 'email' in response

 - **Endpoint:** `POST /users`
 - **Severity:** HIGH
 - **Tests Affected:** 5
 - **Confidence:** 95%

 #### Issue #2: Unexpected field 'internal_id' found in response

 - **Endpoint:** `GET /users/{userId}`
 - **Severity:** MEDIUM
 - **Tests Affected:** 3
 - **Confidence:** 88%

 #### Issue #3: Type mismatch: field 'age' expected integer, got string

 - **Endpoint:** `POST /users`
 - **Severity:** HIGH
 - **Tests Affected:** 4
 - **Confidence:** 92%
