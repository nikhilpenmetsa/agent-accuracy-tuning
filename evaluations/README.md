# Agent Evaluation Framework

This directory contains test questions and evaluation tools for measuring and improving the HR assistant agent's accuracy.

## Test Question Categories

### 1. Simple Factual (sf-*)
Basic questions that should be answered directly from KB without case creation.
- Tests: KB search accuracy, no unnecessary escalation
- Expected: Quick, accurate answers

### 2. Policy Clarification (pc-*)
Questions requiring KB search to explain policies and procedures.
- Tests: KB retrieval, answer completeness, no case creation
- Expected: Detailed policy explanations

### 3. Explicit Case Requests (ec-*)
Clear requests to create cases or submit formal requests.
- Tests: Case creation when appropriate
- Expected: Gather details, create case, confirm

### 4. Ambiguous (am-*)
Vague questions requiring clarification before action.
- Tests: Judgment, clarifying questions, conditional case creation
- Expected: Ask questions before deciding action

### 5. Multi-Turn (mt-*)
Conversations testing context maintenance across multiple turns.
- Tests: Memory, context awareness, avoiding redundant searches
- Expected: Maintain conversation context

### 6. Complex Policy (cp-*)
Questions spanning multiple documents or requiring synthesis.
- Tests: Multi-document retrieval, answer synthesis
- Expected: Comprehensive answers from multiple sources

### 7. Edge Cases (edge-*)
Situations requiring judgment about escalation.
- Tests: Severity assessment, appropriate escalation
- Expected: Right balance of help vs. escalation

### 8. Should Not Create Cases (sncc-*)
Questions that should never result in case creation.
- Tests: Over-escalation prevention
- Expected: Information only, no cases

### 9. Context Maintenance (cm-*)
Multi-turn conversations testing context tracking.
- Tests: Conversation memory, avoiding redundant tool calls
- Expected: Efficient, context-aware responses

### 10. Tool Selection (ts-*)
Questions testing correct tool usage.
- Tests: Choosing right tool for the task
- Expected: list_cases vs. create_case vs. search_kb

### 11. Negative Tests (neg-*)
Out-of-scope questions the agent should decline.
- Tests: Scope boundaries, graceful decline
- Expected: Polite refusal, redirect to HR topics

### 12. Accuracy Tests (acc-*)
Questions with specific correct answers for validation.
- Tests: Factual accuracy, numeric precision
- Expected: Exact correct information

## Evaluation Metrics

### Primary Metrics

**Tool Call Accuracy:**
- Precision: Correct tool calls / Total tool calls
- Recall: Correct tool calls / Should have called tool
- F1 Score: Harmonic mean of precision and recall

**Case Creation Accuracy:**
- False Positive Rate: Unnecessary cases / Total questions
- False Negative Rate: Missing cases / Should have created
- Appropriate Creation Rate: Correct cases / Total cases

**Answer Accuracy:**
- Factual Correctness: Correct answers / Total questions
- Completeness: Contains expected keywords / Total questions
- Hallucination Rate: Incorrect info / Total responses

### Secondary Metrics

**Efficiency:**
- Average turns to resolution
- Redundant KB searches
- Context maintenance score

**User Experience:**
- Clarifying questions when needed
- Appropriate tone and helpfulness
- Response length (concise vs. verbose)

## Running Evaluations

### Manual Testing

1. Load test questions from `test_questions.json`
2. Ask each question through the frontend
3. Record agent behavior:
   - Tools called
   - Cases created
   - Answer accuracy
   - Number of turns
4. Compare against expected behavior
5. Calculate metrics

### Automated Testing (Future)

Create evaluation script that:
- Iterates through test questions
- Calls agent API directly
- Parses responses for tool calls
- Validates against expected behavior
- Generates metrics report

## Tuning Workflow

1. **Baseline**: Run full test set, record metrics
2. **Identify Issues**: Find patterns in failures
3. **Hypothesize**: Determine what to tune (prompt, model, policy)
4. **Implement**: Make changes to agent configuration
5. **Test**: Re-run test set
6. **Measure**: Compare metrics to baseline
7. **Iterate**: Repeat until targets met

## Target Metrics (Goals)

- Case Creation False Positive Rate: < 10%
- Case Creation False Negative Rate: < 5%
- Answer Accuracy: > 95%
- KB Search Precision: > 90%
- Context Maintenance: > 85%

## Test Question Design Principles

1. **Realistic**: Questions users would actually ask
2. **Specific**: Clear expected behavior
3. **Measurable**: Objective success criteria
4. **Diverse**: Cover all agent capabilities
5. **Edge Cases**: Test boundary conditions
6. **Progressive**: Simple to complex

## Adding New Test Questions

When adding questions:
1. Assign unique ID with category prefix
2. Define expected behavior clearly
3. Include expected answer keywords
4. Add notes explaining the test purpose
5. Ensure question is realistic

## Files

- `test_questions.json`: Complete test question set
- `README.md`: This file
- `evaluation_results/`: Directory for test run results (create as needed)
- `tuning_log.md`: Track tuning iterations and results (create as needed)

## Next Steps

1. Run baseline evaluation with current agent
2. Document results in `evaluation_results/baseline.json`
3. Identify top 3 accuracy issues
4. Create tuning hypotheses
5. Iterate on improvements
