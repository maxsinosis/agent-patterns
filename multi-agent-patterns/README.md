# 🤝 Multi-Agent Coordination Patterns

Split work across specialized agents to reduce context bloat and save tokens.

## The Problem

Single-agent systems load everything on every request:
- Business rules + dev docs + finance data + project context = 10KB+
- At 100 requests/day: 1M tokens = $5/day = $150/month

**That's $1,800/year just on context overhead.**

## Pattern 1: Coordinator + Specialists

Main agent stays lightweight, spawns specialists on-demand.

```
┌─────────────┐
│ Main Agent  │  <-- User communication, routing, coordination
│   (2KB)     │
└──────┬──────┘
       │
       ├──> ┌──────────────┐
       │    │ Finance Agent│  Spawned for revenue tasks
       │    │   (5KB)      │  Dies after completion
       │    └──────────────┘
       │
       ├──> ┌──────────────┐
       │    │ Dev Agent    │  Spawned for code tasks
       │    │   (6KB)      │  Dies after completion
       │    └──────────────┘
       │
       └──> ┌──────────────┐
            │ Content Agent│  Spawned for marketing
            │   (4KB)      │  Dies after completion
            └──────────────┘
```

### When to Split

**Use subagent when:**
- Task needs >5KB of specialized context
- Task will take >5 tool calls
- Task is independent (doesn't need main agent context)

**Keep in main agent when:**
- Simple queries (<3 tool calls)
- Needs user clarification
- Requires cross-domain coordination

### Token Math

**Before (single agent):**
- 10KB context on every request
- 100 requests/day = 1M tokens/day
- Cost: $5/day

**After (coordinator pattern):**
- Main: 2KB × 80 requests = 160K tokens
- Specialists: 5KB × 20 requests = 100K tokens
- Total: 260K tokens/day
- Cost: $1.30/day

**Savings: 74% = $100+/month**

## Pattern 2: Subagent Spawning

Simple implementation - no framework needed.

```python
# Main agent logic
def handle_request(user_message, context):
    task_type = classify_task(user_message)
    
    if task_type == "simple":
        # Handle directly
        return process_simple_task(user_message)
    
    elif task_type == "finance":
        # Spawn specialist
        subagent = spawn_subagent(
            role="finance_specialist",
            context={
                "rules": load_file("rules/finance.md"),
                "recent_data": fetch_recent_transactions(),
            },
            task=user_message
        )
        result = subagent.execute()
        return format_response(result)
    
    elif task_type == "development":
        subagent = spawn_subagent(
            role="dev_specialist",
            context={
                "codebase": get_project_structure(),
                "recent_commits": fetch_recent_commits(),
            },
            task=user_message
        )
        result = subagent.execute()
        return format_response(result)
```

## Pattern 3: Context Handoff

What context should you pass to a subagent?

### ✅ DO Pass:
- **Task description** - what they need to accomplish
- **Specialized rules** - domain-specific guidelines
- **Fresh data** - recent relevant information
- **Output format** - how to report back

### ❌ DON'T Pass:
- **Full conversation history** - subagent doesn't need it
- **Unrelated projects** - stay focused
- **Main agent's identity** - subagent has its own role
- **User preferences** - unless task-relevant

### Example Context Handoff

```python
# ❌ BAD: Pass everything
subagent_context = {
    "full_memory": load_file("MEMORY.md"),  # 10KB
    "all_rules": load_file("RULES.md"),     # 8KB
    "chat_history": last_100_messages,       # 15KB
}
# Total: 33KB for a simple task!

# ✅ GOOD: Pass only what's needed
subagent_context = {
    "task": "Calculate Q1 revenue",
    "rules": """
        - Use accrual accounting
        - Include pending invoices
        - Report in USD
    """,
    "data": fetch_q1_transactions(),
}
# Total: ~3KB for the same task
```

## Pattern 4: Subagent Templates

Pre-define specialist roles for consistency.

```python
SUBAGENT_TEMPLATES = {
    "finance": {
        "context_files": ["rules/finance.md", "rules/reporting.md"],
        "data_sources": ["transactions", "invoices", "revenue"],
        "output_format": "structured_report",
        "max_tokens": 5000,
    },
    "developer": {
        "context_files": ["rules/code-style.md", "architecture.md"],
        "data_sources": ["git_log", "open_prs", "issues"],
        "output_format": "technical_summary",
        "max_tokens": 8000,
    },
    "content": {
        "context_files": ["brand-voice.md", "content-guidelines.md"],
        "data_sources": ["recent_posts", "audience_metrics"],
        "output_format": "ready_to_publish",
        "max_tokens": 4000,
    },
}

def spawn_subagent(role, task):
    template = SUBAGENT_TEMPLATES[role]
    context = {
        "role": role,
        "task": task,
        **load_context_from_template(template)
    }
    return Subagent(context)
```

## Pattern 5: Error Handling

Subagents can fail. Handle it gracefully.

```python
def execute_with_fallback(subagent, task):
    try:
        result = subagent.execute(timeout=30)
        return result
    
    except TimeoutError:
        # Subagent took too long
        log_error("Subagent timeout", task)
        return fallback_to_main_agent(task)
    
    except SubagentError as e:
        # Subagent couldn't complete task
        log_error("Subagent failed", e)
        return ask_user_for_clarification(task)
    
    finally:
        # Always clean up
        subagent.terminate()
```

## Real-World Example

**Scenario:** User asks "How's our revenue looking this month?"

### Single-Agent Approach:
```
1. Load full MEMORY.md (10KB)
2. Load finance rules (5KB)
3. Load dev rules (unnecessary, 6KB)
4. Load content guidelines (unnecessary, 4KB)
5. Fetch revenue data
6. Calculate and respond

Total tokens: ~7,000 (context + processing)
```

### Multi-Agent Approach:
```
Main agent (2KB context):
1. Recognize finance query
2. Spawn finance subagent

Finance subagent (5KB context):
1. Load ONLY finance rules (5KB)
2. Fetch revenue data
3. Calculate
4. Report back to main agent
5. Terminate

Main agent:
1. Format response to user

Total tokens: ~3,000 (context + processing)
Savings: 57%
```

## When NOT to Use This Pattern

- **Rapid back-and-forth:** If user will ask 10 follow-ups, keep one agent alive
- **Cross-domain tasks:** If task needs finance AND dev context, single agent might be simpler
- **Very simple operations:** Don't spawn a subagent to add 2+2

## Implementation Checklist

- [ ] Identify 3-5 distinct domains in your agent's work
- [ ] Measure current context size per domain
- [ ] Create subagent templates for each domain
- [ ] Implement spawn + execute + terminate pattern
- [ ] Add timeout and error handling
- [ ] Monitor token usage before/after
- [ ] Iterate on context handoff (what to pass/skip)

## Token Savings Summary

| Setup | Context/Request | 100 req/day | Monthly Cost |
|-------|----------------|-------------|--------------|
| Single agent | 10KB | 1M tokens | $150 |
| Coordinator (naive) | 8KB | 800K tokens | $120 |
| Coordinator (optimized) | 2.6KB | 260K tokens | $39 |

**Potential savings: 74% = $111/month**

---

**Questions? Issues? Found this useful?**

⭐ Star the repo: https://github.com/maxsinosis/agent-patterns  
💝 Support on Ko-fi: https://ko-fi.com/maxsinosis

*More patterns coming soon.*
