# How to Run an Evaluation

This guide walks through the process of evaluating the HR assistant agent using the test question set.

## Prerequisites

- Agent deployed to AgentCore Runtime
- Frontend deployed and accessible
- Test user credentials available
- Access to CloudWatch logs for detailed analysis

## Evaluation Process

### Step 1: Prepare

1. **Create a new evaluation file:**
   ```bash
   cp evaluations/evaluation_template.md evaluations/results/eval-YYYY-MM-DD-description.md
   ```

2. **Document current configuration:**
   - Note agent version/commit
   - Record system prompt
   - Note model parameters (temperature, etc.)
   - Document any recent changes

3. **Clear previous test data (optional):**
   - Delete test cases from DynamoDB
   - Start fresh session in frontend

### Step 2: Run Tests

**For each test question:**

1. **Open frontend** in browser
2. **Start new session** (or continue if testing multi-turn)
3. **Ask the question** exactly as written in test_questions.json
4. **Observe agent behavior:**
   - What tools did it call? (check CloudWatch or frontend network tab)
   - Did it search the knowledge base?
   - Did it create a case?
   - Did it ask clarifying questions?
   - How many turns to resolution?

5. **Record results** in your evaluation file:
   - Mark ✓ or ✗ for each expected behavior
   - Note actual answer provided
   - Add observations in Notes column

6. **For multi-turn conversations:**
   - Keep same session
   - Ask follow-up questions in sequence
   - Track context maintenance

### Step 3: Analyze Tool Calls

**Check CloudWatch Logs:**
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/askhragent-xxx-DEFAULT --follow
```

Look for:
- `search_knowledge_base` calls
- `create_case` calls
- `list_cases` calls
- Tool parameters and results

**Check DynamoDB Cases Table:**
```bash
aws dynamodb scan --table-name hr-assistant-case-backend-stack-cases \
  --filter-expression "attribute_exists(session_id)"
```

Count cases created during evaluation.

### Step 4: Calculate Metrics

**KB Search Accuracy:**
- Count questions where KB search was expected
- Count questions where KB search occurred
- Calculate precision and recall

**Case Creation Accuracy:**
- Count questions where case should be created
- Count questions where case was created
- Identify false positives (unnecessary cases)
- Identify false negatives (missing cases)

**Answer Accuracy:**
- For each question, check if answer contains expected keywords
- For accuracy tests (acc-*), verify specific values are correct
- Note any hallucinations or incorrect information

**Context Maintenance:**
- For multi-turn conversations, check if context was maintained
- Count redundant KB searches
- Note if agent "forgot" previous context

### Step 5: Document Findings

**In your evaluation file:**

1. **Fill in Summary Metrics section**
   - Calculate percentages
   - Compare to target metrics

2. **List Issues Identified**
   - Group by priority
   - Note patterns (e.g., "creates cases for all benefit questions")

3. **Add Tuning Recommendations**
   - Specific prompt changes
   - Model parameter adjustments
   - Tool policy modifications

## Tips for Effective Evaluation

### Be Consistent
- Ask questions exactly as written
- Use same test user for all questions
- Test in same environment

### Document Everything
- Screenshot interesting behaviors
- Copy full agent responses
- Note any errors or unexpected behavior

### Look for Patterns
- Does agent always create cases for certain topics?
- Does it search KB unnecessarily?
- Does it lose context after certain types of questions?

### Test Edge Cases Carefully
- These require judgment calls
- Document your reasoning for expected behavior
- Note if agent's judgment seems reasonable even if different

## Common Issues to Watch For

### Over-Escalation
- Creating cases for simple questions
- Searching KB when answer should be in memory
- Not using conversation context

### Under-Escalation
- Not creating cases when explicitly requested
- Not searching KB when needed
- Providing incorrect information instead of searching

### Context Loss
- Re-searching for information already discussed
- Not maintaining topic across turns
- Forgetting user's situation

### Tool Misuse
- Using create_case when should use list_cases
- Multiple redundant KB searches
- Not using tools when needed

## After Evaluation

### 1. Calculate Overall Score
```
Overall Accuracy = (Correct Behaviors / Total Expected Behaviors) × 100%
```

### 2. Identify Top 3 Issues
Focus on highest-impact problems:
- Highest false positive rate
- Most common failure pattern
- Biggest user experience issue

### 3. Create Tuning Hypothesis
Example:
```
Issue: Agent creates cases for 40% of policy questions
Hypothesis: System prompt doesn't clearly distinguish information vs. action requests
Proposed Fix: Add explicit guidelines: "Only create cases when user explicitly requests 
to submit, file, create, or open a case/ticket/request"
```

### 4. Implement Changes
- Update agent code (main.py)
- Redeploy to AgentCore
- Document changes in tuning log

### 5. Re-evaluate
- Run same test set
- Compare metrics to previous run
- Iterate until targets met

## Evaluation Frequency

**Recommended schedule:**
- Baseline: Before any tuning
- After each tuning iteration
- Before production release
- Monthly in production (sample of questions)

## Storing Results

Save evaluation files in:
```
evaluations/results/
├── baseline-2026-02-25.md
├── v1.1-reduced-cases-2026-02-26.md
├── v1.2-improved-context-2026-02-27.md
└── ...
```

## Automated Evaluation (Future Enhancement)

Consider building a script that:
1. Reads test_questions.json
2. Calls agent API for each question
3. Parses responses and tool calls
4. Calculates metrics automatically
5. Generates evaluation report

This would enable:
- Faster iteration cycles
- Consistent evaluation methodology
- Regression testing
- A/B testing different configurations

## Questions?

Contact the agent development team or refer to the main README.md for architecture details.
