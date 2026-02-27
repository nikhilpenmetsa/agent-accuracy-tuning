# Evaluation Run Template

**Date:** YYYY-MM-DD
**Agent Version:** (e.g., baseline, v1.1-reduced-case-creation)
**Model:** (e.g., Claude 3.5 Sonnet)
**Temperature:** (e.g., 0.3)
**Evaluator:** (your name)

## Configuration

**System Prompt Changes:**
```
(paste relevant prompt sections or note "baseline")
```

**Model Parameters:**
- Temperature: 
- Top-p: 
- Top-k: 
- Max tokens: 

**Tool Policies:**
```
(note any changes to tool usage guidelines)
```

## Test Results

### Simple Factual Questions (sf-*)

| ID | Question | KB Search | Case Created | Answer Correct | Notes |
|----|----------|-----------|--------------|----------------|-------|
| sf-001 | How many PTO days... | ✓/✗ | ✓/✗ | ✓/✗ | |
| sf-002 | What's the 401k match... | ✓/✗ | ✓/✗ | ✓/✗ | |
| sf-003 | When is open enrollment... | ✓/✗ | ✓/✗ | ✓/✗ | |
| sf-004 | What holidays... | ✓/✗ | ✓/✗ | ✓/✗ | |
| sf-005 | Standard work week... | ✓/✗ | ✓/✗ | ✓/✗ | |

### Policy Clarification (pc-*)

| ID | Question | KB Search | Case Created | Answer Correct | Notes |
|----|----------|-----------|--------------|----------------|-------|
| pc-001 | Can I work remotely... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-002 | Dress code... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-003 | Submit expense report... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-004 | Dental insurance... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-005 | Expense rental car... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-006 | Meal allowance... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-007 | Update address Workday... | ✓/✗ | ✓/✗ | ✓/✗ | |
| pc-008 | 401k vesting... | ✓/✗ | ✓/✗ | ✓/✗ | |

### Explicit Case Requests (ec-*)

| ID | Question | KB Search | Case Created | Gathered Details | Notes |
|----|----------|-----------|--------------|------------------|-------|
| ec-001 | Parental leave request... | ✓/✗ | ✓/✗ | ✓/✗ | |
| ec-002 | Create case for benefits... | ✓/✗ | ✓/✗ | ✓/✗ | |
| ec-003 | File harassment complaint... | ✓/✗ | ✓/✗ | ✓/✗ | |
| ec-004 | Open ticket for expense... | ✓/✗ | ✓/✗ | ✓/✗ | |
| ec-005 | Report safety issue... | ✓/✗ | ✓/✗ | ✓/✗ | |

### Ambiguous Questions (am-*)

| ID | Question | Asked Clarifying Q | Case Created | Appropriate Action | Notes |
|----|----------|-------------------|--------------|-------------------|-------|
| am-001 | Problem with paycheck... | ✓/✗ | ✓/✗ | ✓/✗ | |
| am-002 | Manager not following policy... | ✓/✗ | ✓/✗ | ✓/✗ | |
| am-003 | Need help with benefits... | ✓/✗ | ✓/✗ | ✓/✗ | |
| am-004 | Issues with performance review... | ✓/✗ | ✓/✗ | ✓/✗ | |
| am-005 | Wrong with time off request... | ✓/✗ | ✓/✗ | ✓/✗ | |

### Multi-Turn Conversations (mt-*)

| ID | Description | Context Maintained | Redundant Searches | Turns to Resolution | Notes |
|----|-------------|-------------------|-------------------|---------------------|-------|
| mt-001 | PTO policy conversation | ✓/✗ | Count | # | |
| mt-002 | Medical insurance options | ✓/✗ | Count | # | |
| mt-003 | Travel policy conversation | ✓/✗ | Count | # | |

### Complex Policy (cp-*)

| ID | Question | KB Search | Multi-Doc | Answer Complete | Notes |
|----|----------|-----------|-----------|-----------------|-------|
| cp-001 | Benefits during parental leave... | ✓/✗ | ✓/✗ | ✓/✗ | |
| cp-002 | PTO and 401k at 4 years... | ✓/✗ | ✓/✗ | ✓/✗ | |
| cp-003 | Rental car Chicago trip... | ✓/✗ | ✓/✗ | ✓/✗ | |
| cp-004 | Total compensation... | ✓/✗ | ✓/✗ | ✓/✗ | |
| cp-005 | Relocation salary impact... | ✓/✗ | ✓/✗ | ✓/✗ | |

### Edge Cases (edge-*)

| ID | Question | Appropriate Response | Case Created | Notes |
|----|----------|---------------------|--------------|-------|
| edge-001 | Unhappy with review... | ✓/✗ | ✓/✗ | |
| edge-002 | Expense report denied... | ✓/✗ | ✓/✗ | |
| edge-003 | Discrimination... | ✓/✗ | ✓/✗ | |
| edge-004 | PTO denied for wedding... | ✓/✗ | ✓/✗ | |
| edge-005 | Haven't been paid... | ✓/✗ | ✓/✗ | |

### Should Not Create Cases (sncc-*)

| ID | Question | Case Created | Answer Provided | Notes |
|----|----------|--------------|-----------------|-------|
| sncc-001 | How to request time off... | ✓/✗ | ✓/✗ | |
| sncc-002 | What's covered under EAP... | ✓/✗ | ✓/✗ | |
| sncc-003 | When do merit increases... | ✓/✗ | ✓/✗ | |
| sncc-004 | Tuition reimbursement... | ✓/✗ | ✓/✗ | |
| sncc-005 | Health insurance plans... | ✓/✗ | ✓/✗ | |

### Tool Selection (ts-*)

| ID | Question | Correct Tool Used | Notes |
|----|----------|-------------------|-------|
| ts-001 | Show me my recent cases | ✓/✗ | Should use list_cases |
| ts-002 | What cases have I submitted | ✓/✗ | Should use list_cases |
| ts-003 | Search for remote work | ✓/✗ | Should use search_kb |

### Negative Tests (neg-*)

| ID | Question | Declined Appropriately | Notes |
|----|----------|----------------------|-------|
| neg-001 | Weather today | ✓/✗ | Out of scope |
| neg-002 | Write Python script | ✓/✗ | Out of scope |
| neg-003 | Capital of France | ✓/✗ | Out of scope |

### Accuracy Tests (acc-*)

| ID | Question | Answer Correct | Specific Value Correct | Notes |
|----|----------|----------------|----------------------|-------|
| acc-001 | Hotel rate SF | ✓/✗ | $275 ✓/✗ | |
| acc-002 | Maternity leave length | ✓/✗ | 12 weeks ✓/✗ | |
| acc-003 | Mileage rate | ✓/✗ | $0.67 ✓/✗ | |
| acc-004 | Bereavement grandmother | ✓/✗ | 3 days ✓/✗ | |
| acc-005 | Dev budget | ✓/✗ | $1,500 ✓/✗ | |

## Summary Metrics

### Overall Scores

- **Total Questions:** 
- **KB Search Precision:** ___ / ___ = ___%
- **KB Search Recall:** ___ / ___ = ___%
- **Case Creation Precision:** ___ / ___ = ___%
- **Case Creation Recall:** ___ / ___ = ___%
- **Answer Accuracy:** ___ / ___ = ___%
- **Context Maintenance:** ___ / ___ = ___%

### Case Creation Analysis

- **Appropriate Cases Created:** ___
- **Inappropriate Cases Created (False Positives):** ___
- **Missing Cases (False Negatives):** ___
- **Case Creation Rate:** ___ cases per ___ questions = ___%

### Tool Usage Analysis

- **Total Tool Calls:** ___
- **KB Searches:** ___
- **Case Creations:** ___
- **Case Lists:** ___
- **Redundant Tool Calls:** ___

## Issues Identified

### High Priority
1. 
2. 
3. 

### Medium Priority
1. 
2. 
3. 

### Low Priority
1. 
2. 

## Tuning Recommendations

### Prompt Changes
```
(suggested prompt modifications)
```

### Model Parameter Changes
- Temperature: 
- Other: 

### Tool Policy Changes
```
(suggested tool usage guideline changes)
```

## Next Steps

1. 
2. 
3. 

## Notes

(Any additional observations or insights)

---

**Evaluation completed by:** ___________
**Date:** ___________
**Time spent:** ___________
