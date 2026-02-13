#!/usr/bin/env python3
"""
Multi-Agent Coordinator Pattern

A lightweight main agent that spawns specialized subagents on-demand.

Usage:
    python coordinator.py "Calculate Q1 revenue"
    python coordinator.py "Review last commit"
    python coordinator.py "Draft tweet about AI"

Token savings: ~60-75% compared to single-agent with full context.
"""

import json
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

# ============================================================================
# Subagent Templates
# ============================================================================

SUBAGENT_TEMPLATES = {
    "finance": {
        "role": "Finance Specialist",
        "context_files": ["rules/finance.md", "rules/reporting.md"],
        "data_sources": ["transactions", "invoices"],
        "instructions": """
            You are a finance specialist agent.
            - Use accrual accounting
            - Report in USD
            - Include pending items
            - Format: structured data + brief summary
        """,
        "max_tokens": 5000,
    },
    "developer": {
        "role": "Development Specialist",
        "context_files": ["rules/code-style.md", "ARCHITECTURE.md"],
        "data_sources": ["git_log", "open_issues"],
        "instructions": """
            You are a development specialist agent.
            - Review code for patterns and quality
            - Suggest improvements
            - Check against style guide
            - Format: technical summary + recommendations
        """,
        "max_tokens": 8000,
    },
    "content": {
        "role": "Content Specialist",
        "context_files": ["brand-voice.md", "content-guidelines.md"],
        "data_sources": ["recent_posts", "engagement_metrics"],
        "instructions": """
            You are a content specialist agent.
            - Follow brand voice
            - Optimize for engagement
            - Keep it authentic
            - Format: ready-to-publish content
        """,
        "max_tokens": 4000,
    },
}


# ============================================================================
# Subagent Class
# ============================================================================

@dataclass
class SubagentContext:
    """Minimal context passed to subagent."""
    role: str
    task: str
    instructions: str
    data: Dict[str, Any]
    max_tokens: int


class Subagent:
    """
    A specialized agent that executes a single task and terminates.
    
    In production, this would interface with your LLM API.
    This example simulates the pattern.
    """
    
    def __init__(self, context: SubagentContext):
        self.context = context
        self.start_time = time.time()
        self.is_terminated = False
    
    def execute(self, timeout: int = 30) -> Dict[str, Any]:
        """Execute the task and return results."""
        if self.is_terminated:
            raise RuntimeError("Subagent already terminated")
        
        # Check timeout
        if time.time() - self.start_time > timeout:
            raise TimeoutError(f"Subagent exceeded {timeout}s timeout")
        
        # In production: call LLM with context
        # For this example: simulate processing
        result = self._simulate_execution()
        
        return result
    
    def _simulate_execution(self) -> Dict[str, Any]:
        """Simulate subagent processing (replace with real LLM call)."""
        return {
            "role": self.context.role,
            "task": self.context.task,
            "result": f"[Simulated result for: {self.context.task}]",
            "tokens_used": self.context.max_tokens // 2,
            "completed": True,
        }
    
    def terminate(self):
        """Clean up subagent resources."""
        self.is_terminated = True
        # In production: close connections, clear memory, etc.


# ============================================================================
# Main Coordinator Agent
# ============================================================================

class CoordinatorAgent:
    """
    Lightweight main agent that routes tasks to specialists.
    
    Context: ~2KB (minimal, always loaded)
    Subagents: 4-8KB each (loaded only when needed)
    """
    
    def __init__(self):
        self.context_size = 2048  # bytes (minimal core context)
        self.total_tokens_used = 0
    
    def process_request(self, user_message: str) -> str:
        """Route user request to appropriate handler."""
        
        # Classify task (in production: use LLM or simple rules)
        task_type = self._classify_task(user_message)
        
        # Track tokens for main agent context
        self.total_tokens_used += self.context_size // 4  # ~500 tokens
        
        if task_type == "simple":
            return self._handle_simple_task(user_message)
        
        elif task_type in SUBAGENT_TEMPLATES:
            return self._handle_with_subagent(task_type, user_message)
        
        else:
            return self._handle_unknown_task(user_message)
    
    def _classify_task(self, message: str) -> str:
        """Classify task type from user message."""
        message_lower = message.lower()
        
        # Simple keyword-based classification
        if any(word in message_lower for word in ["revenue", "finance", "money", "profit"]):
            return "finance"
        
        elif any(word in message_lower for word in ["code", "commit", "pr", "bug", "deploy"]):
            return "developer"
        
        elif any(word in message_lower for word in ["tweet", "post", "content", "write"]):
            return "content"
        
        elif any(word in message_lower for word in ["hi", "hello", "help", "what can you"]):
            return "simple"
        
        else:
            return "unknown"
    
    def _handle_simple_task(self, message: str) -> str:
        """Handle simple queries directly (no subagent needed)."""
        # Track a small amount of processing tokens
        self.total_tokens_used += 100
        
        return json.dumps({
            "handler": "main_agent",
            "response": f"Quick answer to: {message}",
            "tokens_used": self.context_size // 4 + 100,
        }, indent=2)
    
    def _handle_with_subagent(self, agent_type: str, task: str) -> str:
        """Spawn specialist subagent to handle task."""
        
        template = SUBAGENT_TEMPLATES[agent_type]
        
        # Build minimal context for subagent
        context = SubagentContext(
            role=template["role"],
            task=task,
            instructions=template["instructions"],
            data=self._fetch_relevant_data(template["data_sources"]),
            max_tokens=template["max_tokens"],
        )
        
        # Spawn and execute
        subagent = Subagent(context)
        
        try:
            result = subagent.execute(timeout=30)
            
            # Track tokens
            subagent_tokens = result.get("tokens_used", 2000)
            self.total_tokens_used += subagent_tokens
            
            return json.dumps({
                "handler": f"{agent_type}_subagent",
                "role": template["role"],
                "result": result["result"],
                "tokens_used": self.context_size // 4 + subagent_tokens,
                "subagent_terminated": True,
            }, indent=2)
        
        except TimeoutError:
            return json.dumps({
                "error": "Subagent timeout",
                "fallback": "Task took too long, please try again or break into smaller steps",
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "fallback": "Something went wrong, please rephrase or try again",
            }, indent=2)
        
        finally:
            subagent.terminate()
    
    def _handle_unknown_task(self, message: str) -> str:
        """Handle tasks that don't match any specialist."""
        self.total_tokens_used += 200
        
        return json.dumps({
            "handler": "main_agent",
            "response": f"I'm not sure how to handle: {message}",
            "suggestion": "Try asking about finance, development, or content tasks",
            "tokens_used": self.context_size // 4 + 200,
        }, indent=2)
    
    def _fetch_relevant_data(self, sources: list) -> Dict[str, Any]:
        """
        Fetch only the data needed for this specific task.
        In production: query databases, APIs, files, etc.
        """
        # Simulate fetching data
        return {
            source: f"[Sample data from {source}]"
            for source in sources
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Return usage statistics."""
        return {
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self.total_tokens_used * 0.000005,  # $5/million tokens
        }


# ============================================================================
# Token Comparison Demo
# ============================================================================

def compare_token_usage():
    """
    Demonstrate token savings: single agent vs coordinator pattern.
    """
    
    print("\n" + "="*70)
    print("TOKEN USAGE COMPARISON: Single Agent vs Multi-Agent Coordinator")
    print("="*70)
    
    test_tasks = [
        "Hi, what can you help with?",
        "Calculate Q1 revenue",
        "Review the last commit",
        "Draft a tweet about AI agents",
        "What's our profit margin?",
    ]
    
    # Single-agent simulation (loads everything every time)
    single_agent_context = 10_000  # 10KB context = ~2500 tokens
    single_agent_tokens = 0
    
    print("\n📦 SINGLE AGENT (loads full 10KB context every request):")
    for task in test_tasks:
        tokens = single_agent_context // 4 + 500  # context + processing
        single_agent_tokens += tokens
        print(f"  • {task[:50]:50} → {tokens:,} tokens")
    
    print(f"\n  TOTAL: {single_agent_tokens:,} tokens")
    print(f"  COST:  ${single_agent_tokens * 0.000005:.4f}")
    
    # Multi-agent coordinator
    coordinator = CoordinatorAgent()
    
    print("\n🤝 COORDINATOR + SUBAGENTS (loads minimal context + specialists):")
    for task in test_tasks:
        result = coordinator.process_request(task)
        result_data = json.loads(result)
        tokens = result_data.get("tokens_used", 0)
        handler = result_data.get("handler", "unknown")
        print(f"  • {task[:50]:50} → {tokens:,} tokens ({handler})")
    
    stats = coordinator.get_stats()
    print(f"\n  TOTAL: {stats['total_tokens_used']:,} tokens")
    print(f"  COST:  ${stats['estimated_cost']:.4f}")
    
    # Calculate savings
    savings_tokens = single_agent_tokens - stats['total_tokens_used']
    savings_percent = (savings_tokens / single_agent_tokens) * 100
    
    print(f"\n💰 SAVINGS:")
    print(f"  Tokens saved: {savings_tokens:,} ({savings_percent:.1f}%)")
    print(f"  Cost saved:   ${savings_tokens * 0.000005:.4f}")
    print(f"\n  At 100 requests/day:")
    print(f"    Single agent: ${single_agent_tokens * 100 * 0.000005:.2f}/day = ${single_agent_tokens * 100 * 0.000005 * 30:.2f}/month")
    print(f"    Coordinator:  ${stats['total_tokens_used'] * 100 * 0.000005:.2f}/day = ${stats['total_tokens_used'] * 100 * 0.000005 * 30:.2f}/month")
    print(f"    MONTHLY SAVINGS: ${savings_tokens * 100 * 0.000005 * 30:.2f}")
    print("="*70 + "\n")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Process single task
        coordinator = CoordinatorAgent()
        user_input = " ".join(sys.argv[1:])
        result = coordinator.process_request(user_input)
        print(result)
    else:
        # Run comparison demo
        compare_token_usage()
