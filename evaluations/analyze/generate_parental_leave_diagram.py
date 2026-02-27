"""Sequence diagram for parental leave request session."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(1, 1, figsize=(22, 36))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
fig.patch.set_facecolor('white')

# Colors
C_USER = '#4A90D9'
C_AGENT = '#E67E22'
C_MEMORY = '#27AE60'
C_LLM = '#8E44AD'
C_KB = '#E74C3C'
C_CASE = '#2980B9'
C_SSM = '#95A5A6'
C_BG = '#F8F9FA'
C_ARROW = '#2C3E50'

# Swimlane positions
LANES = {
    'User': 10,
    'AgentCore\nRuntime': 28,
    'AgentCore\nMemory': 46,
    'Claude 3.5\nSonnet': 64,
    'Bedrock KB\n& Case API': 84,
}
LANE_COLORS = {
    'User': C_USER,
    'AgentCore\nRuntime': C_AGENT,
    'AgentCore\nMemory': C_MEMORY,
    'Claude 3.5\nSonnet': C_LLM,
    'Bedrock KB\n& Case API': C_KB,
}

# Draw lane headers
for name, x in LANES.items():
    color = LANE_COLORS[name]
    ax.add_patch(mpatches.FancyBboxPatch((x - 7.5, 97), 15, 2.5, boxstyle="round,pad=0.3",
                                          facecolor=color, edgecolor='white', alpha=0.9))
    ax.text(x, 98.25, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')

# Lifelines
for name, x in LANES.items():
    ax.plot([x, x], [97, 0.5], color='#BDC3C7', linewidth=0.7, linestyle='--', zorder=0)


def arrow(fr, to, y, label, color=C_ARROW, fontsize=6.5, bold=False):
    x1, x2 = LANES[fr], LANES[to]
    d = 1 if x2 > x1 else -1
    ax.annotate('', xy=(x2 - d * 0.5, y), xytext=(x1 + d * 0.5, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.1))
    mid = (x1 + x2) / 2
    w = 'bold' if bold else 'normal'
    ax.text(mid, y + 0.25, label, ha='center', va='bottom', fontsize=fontsize, color=color, fontweight=w)


def note(x, y, text, color='#6C757D'):
    ax.text(x, y, text, ha='center', va='center', fontsize=5.8, color=color,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#F0E0A0', alpha=0.9))


def phase(y_top, y_bot, label, sub=''):
    ax.add_patch(mpatches.FancyBboxPatch((1, y_bot - 0.15), 98, y_top - y_bot + 0.3,
                                          boxstyle="round,pad=0.15", facecolor=C_BG,
                                          edgecolor='#DEE2E6', alpha=0.5, zorder=0))
    ax.text(2.2, y_top, label, ha='left', va='top', fontsize=7, fontweight='bold', color='#495057')
    if sub:
        ax.text(2.2, y_top - 0.7, sub, ha='left', va='top', fontsize=6, color='#6C757D', style='italic')


# ============================================================
y = 96

# PHASE 1: Request + SSM
phase(96, 94, 'Phase 1: Request Arrives', '192ms')
arrow('User', 'AgentCore\nRuntime', y, '"I need to submit a request for parental leave"', C_USER, bold=True)
y -= 0.9
note(28, y - 0.3, '4x SSM.GetParameter (model, memory, KB, API config)', C_SSM)

# PHASE 2: Session Init
y -= 1.8
phase(y + 0.3, y - 3.5, 'Phase 2: Session Initialization', '6 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '2x ListEvents - read_session() [new + legacy format]', C_MEMORY)
y -= 1.0
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent - create_session()', C_MEMORY)
y -= 1.0
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '2x ListEvents - read_agent()', C_MEMORY)
y -= 1.0
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent - create_agent()', C_MEMORY)

# PHASE 3: Memory Retrieval
y -= 1.6
phase(y + 0.3, y - 3.0, 'Phase 3: Memory Retrieval', '3x RetrieveMemoryRecords')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent - save user message', C_MEMORY)
y -= 0.9
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '2x ListEvents + 1x CreateEvent - state update', C_MEMORY)
y -= 1.0
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '3x RetrieveMemoryRecords (preferences, facts, summaries)', C_MEMORY, bold=True)
y -= 0.8
note(46, y, 'Found: promotion dispute + Diwali holiday request from prior sessions', C_MEMORY)

# PHASE 4: LLM #1 -> KB Search
y -= 1.6
phase(y + 0.3, y - 3.5, 'Phase 4: LLM Call #1 — Decides to search KB first', '1,220 → 101 tokens · 5.8s')
arrow('AgentCore\nRuntime', 'Claude 3.5\nSonnet', y, 'system prompt + 4 tools + <user_context> + question', C_LLM, bold=True)
y -= 0.8
note(64, y, '1,220 input tokens | temp=0.3', C_LLM)
y -= 1.0
arrow('Claude 3.5\nSonnet', 'AgentCore\nRuntime', y, 'tool_use: search_hr_knowledge_base("parental leave policy benefits")', C_LLM, bold=True)
y -= 0.7
note(46, y, '"I\'ll help you submit a parental leave request... let me check the KB"', '#495057')

# State update
y -= 1.2
phase(y + 0.3, y - 0.7, 'State Update', '4 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent', C_MEMORY)

# PHASE 5: KB Search
y -= 1.5
phase(y + 0.3, y - 1.8, 'Phase 5: Tool #1 — KB Search', '~1s')
arrow('AgentCore\nRuntime', 'Bedrock KB\n& Case API', y, 'Bedrock Agent Runtime.Retrieve("parental leave policy benefits")', C_KB, bold=True)
y -= 1.0
arrow('Bedrock KB\n& Case API', 'AgentCore\nRuntime', y, 'Policy: 12wk birth mothers, 6wk non-birth/adoptive, within 12mo', C_KB)

# State update
y -= 1.2
phase(y + 0.3, y - 0.7, 'State Update', '4 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent', C_MEMORY)

# PHASE 6: LLM #2 -> get_available_case_types
y -= 1.5
phase(y + 0.3, y - 3.0, 'Phase 6: LLM Call #2 — Checks case types', '2,932 → 80 tokens · 3.2s')
arrow('AgentCore\nRuntime', 'Claude 3.5\nSonnet', y, 'prompt + KB results (3 messages now)', C_LLM, bold=True)
y -= 1.0
arrow('Claude 3.5\nSonnet', 'AgentCore\nRuntime', y, 'tool_use: get_available_case_types()', C_LLM, bold=True)
y -= 0.7
note(46, y, '"Let me help you create a case for your parental leave request"', '#495057')

# State update
y -= 1.2
phase(y + 0.3, y - 0.7, 'State Update', '4 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent', C_MEMORY)

# PHASE 7: Case Types API
y -= 1.5
phase(y + 0.3, y - 1.8, 'Phase 7: Tool #2 — Get Case Types', '')
arrow('AgentCore\nRuntime', 'Bedrock KB\n& Case API', y, 'GET /case-types (Case API)', C_CASE, bold=True)
y -= 1.0
arrow('Bedrock KB\n& Case API', 'AgentCore\nRuntime', y, 'Available: pto, benefits, compensation, general, ...', C_CASE)

# State update
y -= 1.2
phase(y + 0.3, y - 0.7, 'State Update', '4 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent', C_MEMORY)

# PHASE 8: LLM #3 -> create_workday_case
y -= 1.5
phase(y + 0.3, y - 3.5, 'Phase 8: LLM Call #3 — Creates the case', '3,298 → 152 tokens · 9.6s')
arrow('AgentCore\nRuntime', 'Claude 3.5\nSonnet', y, 'prompt + KB results + case types (5 messages)', C_LLM, bold=True)
y -= 1.0
arrow('Claude 3.5\nSonnet', 'AgentCore\nRuntime', y, 'tool_use: create_workday_case(type="benefits", desc=...)', C_LLM, bold=True)
y -= 0.8
note(64, y, 'Description enriched with KB policy details:\n"12 weeks birth mothers, 6 weeks non-birth"', C_LLM)
y -= 0.7
note(46, y, '"I\'ll create a case under benefits for your parental leave request"', '#495057')

# State update
y -= 1.2
phase(y + 0.3, y - 0.7, 'State Update', '4 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent', C_MEMORY)

# PHASE 9: Create Case API
y -= 1.5
phase(y + 0.3, y - 1.8, 'Phase 9: Tool #3 — Create Case', '')
arrow('AgentCore\nRuntime', 'Bedrock KB\n& Case API', y, 'POST /cases (type=benefits, desc=parental leave request)', C_CASE, bold=True)
y -= 1.0
arrow('Bedrock KB\n& Case API', 'AgentCore\nRuntime', y, 'Case created: 54a7e7ea-a55f-4d21-b058-96ee3450535d', C_CASE)

# State update
y -= 1.2
phase(y + 0.3, y - 0.7, 'State Update', '4 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent', C_MEMORY)

# PHASE 10: LLM #4 -> Final response
y -= 1.5
phase(y + 0.3, y - 3.0, 'Phase 10: LLM Call #4 — Final Response', '3,714 → 213 tokens · 7.8s')
arrow('AgentCore\nRuntime', 'Claude 3.5\nSonnet', y, 'prompt + all tool results (7 messages)', C_LLM, bold=True)
y -= 1.0
arrow('Claude 3.5\nSonnet', 'AgentCore\nRuntime', y, 'end_turn: policy summary + case ID + next steps', C_LLM, bold=True)
y -= 0.7
note(64, y, '213 tokens | Summarizes policy, case ID, suggests manager discussion', C_LLM)

# PHASE 11: Cleanup
y -= 1.5
phase(y + 0.3, y - 1.2, 'Phase 11: Cleanup + SaveConversation', '5 memory calls')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1x CreateEvent + 2x ListEvents + 1x CreateEvent + SaveConversation', C_MEMORY)

# Response to user
y -= 1.8
arrow('AgentCore\nRuntime', 'User', y, 'Case created (ID: 54a7e7ea...) + policy details + next steps', C_USER, bold=True)

# Summary box
y -= 1.8
lines = [
    "TOTALS:  4 LLM calls (26.4s)  ·  3 tools used  ·  ~40 memory API calls  ·  11,710 tokens (11,164 in + 546 out)",
    "TOOL CHAIN:  search_hr_knowledge_base → get_available_case_types → create_workday_case → respond",
]
ax.add_patch(mpatches.FancyBboxPatch((2, y - 1.5), 96, 2.8, boxstyle="round,pad=0.3",
                                      facecolor='#2C3E50', edgecolor='none', alpha=0.9))
ax.text(50, y, lines[0], ha='center', va='center', fontsize=7.5, color='white', fontweight='bold')
ax.text(50, y - 0.8, lines[1], ha='center', va='center', fontsize=7.5, color='#F39C12', fontweight='bold')

# Title
ax.text(50, 99.7, 'Agent Session Flow: "I need to submit a request for parental leave"',
        ha='center', va='center', fontsize=13, fontweight='bold', color='#2C3E50')

plt.tight_layout()
import os
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parental_leave_sequence_diagram.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path}")
