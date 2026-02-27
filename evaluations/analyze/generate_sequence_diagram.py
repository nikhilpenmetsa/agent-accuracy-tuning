"""Generate a sequence diagram for the agent chat session flow."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(1, 1, figsize=(20, 28))
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
C_SSM = '#95A5A6'
C_BG_PHASE = '#F8F9FA'
C_ARROW = '#2C3E50'

# Swimlane positions (x)
LANES = {
    'User': 12,
    'AgentCore\nRuntime': 30,
    'AgentCore\nMemory': 50,
    'Claude 3.5\nSonnet': 70,
    'Bedrock\nKB': 88,
}
LANE_COLORS = {
    'User': C_USER,
    'AgentCore\nRuntime': C_AGENT,
    'AgentCore\nMemory': C_MEMORY,
    'Claude 3.5\nSonnet': C_LLM,
    'Bedrock\nKB': C_KB,
}

# Draw lane headers
for name, x in LANES.items():
    color = LANE_COLORS[name]
    ax.add_patch(mpatches.FancyBboxPatch((x - 7, 96.5), 14, 3, boxstyle="round,pad=0.3",
                                          facecolor=color, edgecolor='white', alpha=0.9))
    ax.text(x, 98, name, ha='center', va='center', fontsize=9, fontweight='bold', color='white')

# Draw vertical lifelines
for name, x in LANES.items():
    ax.plot([x, x], [96.5, 1], color='#BDC3C7', linewidth=0.8, linestyle='--', zorder=0)

# Helper to draw arrows
def arrow(from_lane, to_lane, y, label, color=C_ARROW, style='->', fontsize=7, bold=False):
    x1 = LANES[from_lane]
    x2 = LANES[to_lane]
    direction = 1 if x2 > x1 else -1
    ax.annotate('', xy=(x2 - direction * 0.5, y), xytext=(x1 + direction * 0.5, y),
                arrowprops=dict(arrowstyle=style, color=color, lw=1.2))
    mid = (x1 + x2) / 2
    weight = 'bold' if bold else 'normal'
    ax.text(mid, y + 0.35, label, ha='center', va='bottom', fontsize=fontsize,
            color=color, fontweight=weight)

def phase_bg(y_top, y_bottom, label, sublabel=''):
    ax.add_patch(mpatches.FancyBboxPatch((1, y_bottom - 0.2), 98, y_top - y_bottom + 0.4,
                                          boxstyle="round,pad=0.2", facecolor=C_BG_PHASE,
                                          edgecolor='#DEE2E6', alpha=0.5, zorder=0))
    ax.text(2.5, y_top - 0.1, label, ha='left', va='top', fontsize=7.5, fontweight='bold', color='#495057')
    if sublabel:
        ax.text(2.5, y_top - 1.0, sublabel, ha='left', va='top', fontsize=6.5, color='#6C757D', style='italic')

def note(x, y, text, color='#6C757D'):
    ax.text(x, y, text, ha='center', va='center', fontsize=6, color=color,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#F0E0A0', alpha=0.9))

# ============================================================
# PHASE 1: Request + SSM
# ============================================================
y = 95
phase_bg(95.5, 92.5, 'Phase 1: Request Arrives', '192ms')

arrow('User', 'AgentCore\nRuntime', y, '"Tell me about medical insurance options"', C_USER, bold=True)
y -= 1.2
note(30, y - 0.3, '4× SSM.GetParameter (192ms)\nLoad config: model ID, memory ID, KB ID, case API URL', C_SSM)

# ============================================================
# PHASE 2: Session Init
# ============================================================
y -= 2.5
phase_bg(y + 0.5, y - 5.5, 'Phase 2: Session Initialization', '6 memory calls · ~500ms')

arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '2× ListEvents — read_session()', C_MEMORY)
note(50, y - 0.7, 'Check if session exists (new format + legacy fallback)', C_MEMORY)

y -= 1.8
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× CreateEvent — create_session()', C_MEMORY)
note(50, y - 0.7, 'Persist session metadata (session ID, actor ID)', C_MEMORY)

y -= 1.8
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '2× ListEvents — read_agent()', C_MEMORY)
note(50, y - 0.7, 'Check if agent record exists (new + legacy)', C_MEMORY)

y -= 1.8
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× CreateEvent — create_agent()', C_MEMORY)

# ============================================================
# PHASE 3: Memory Retrieval
# ============================================================
y -= 2.2
phase_bg(y + 0.5, y - 5.5, 'Phase 3: Memory Retrieval + User Message Save', '4 memory calls · ~700ms')

arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× CreateEvent — save user message', C_MEMORY)

y -= 1.5
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '2× ListEvents + 1× CreateEvent — state update', C_MEMORY)

y -= 1.8
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '3× RetrieveMemoryRecords', C_MEMORY, bold=True)
note(50, y - 0.7, '/preferences → promotion issue\n/facts → Diwali holiday request\n/summaries → empty (new session)', C_MEMORY)

y -= 1.8
note(40, y, '→ Memory results injected as <user_context> block into prompt', '#E67E22')

# ============================================================
# PHASE 4: LLM Call #1
# ============================================================
y -= 1.8
phase_bg(y + 0.5, y - 4.0, 'Phase 4: LLM Call #1 — Tool Selection', '1,217→78 tokens · 4.2s')

arrow('AgentCore\nRuntime', 'Claude 3.5\nSonnet', y, 'ConverseStream (system prompt + tools + <user_context> + question)', C_LLM, bold=True)
note(70, y - 0.8, '1,217 input tokens\nSystem: AskHR persona (1,282 chars)\nTools: 4 tool definitions\nTemp: 0.3', C_LLM)

y -= 2.5
arrow('Claude 3.5\nSonnet', 'AgentCore\nRuntime', y, 'tool_use: search_hr_knowledge_base("medical insurance plans...")', C_LLM, bold=True)
note(70, y - 0.7, '78 output tokens · stop_reason: tool_use', C_LLM)

# ============================================================
# PHASE 5: Post-LLM state
# ============================================================
y -= 2.2
phase_bg(y + 0.5, y - 1.5, 'Phase 5: Post-LLM #1 State Update', '4 memory calls · ~400ms')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× CreateEvent + 2× ListEvents + 1× CreateEvent', C_MEMORY)

# ============================================================
# PHASE 6: Tool Execution
# ============================================================
y -= 2.5
phase_bg(y + 0.5, y - 2.5, 'Phase 6: Tool Execution — KB Search', '1.1s')

arrow('AgentCore\nRuntime', 'Bedrock\nKB', y, 'search_hr_knowledge_base("medical insurance plans options coverage benefits")', C_KB, bold=True)

y -= 1.5
arrow('Bedrock\nKB', 'AgentCore\nRuntime', y, 'Benefits Overview doc (relevance: 0.41) — Plan A/B/C details', C_KB)

# ============================================================
# PHASE 7: Post-tool state
# ============================================================
y -= 2.2
phase_bg(y + 0.5, y - 1.5, 'Phase 7: Post-Tool State Update', '4 memory calls · ~400ms')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× CreateEvent + 2× ListEvents + 1× CreateEvent', C_MEMORY)

# ============================================================
# PHASE 8: LLM Call #2
# ============================================================
y -= 2.5
phase_bg(y + 0.5, y - 4.5, 'Phase 8: LLM Call #2 — Response Generation', '2,835→449 tokens · 8.3s')

arrow('AgentCore\nRuntime', 'Claude 3.5\nSonnet', y, 'ConverseStream (same prompt + tool_use msg + KB results)', C_LLM, bold=True)
note(70, y - 0.8, '2,835 input tokens (3 messages now)\n+1,618 tokens from KB content', C_LLM)

y -= 2.8
arrow('Claude 3.5\nSonnet', 'AgentCore\nRuntime', y, 'Full response: Plan A (PPO Plus), Plan B (PPO Standard), Plan C (HDHP)', C_LLM, bold=True)
note(70, y - 0.7, '449 output tokens · stop_reason: end_turn', C_LLM)

# ============================================================
# PHASE 9: Cleanup
# ============================================================
y -= 2.5
phase_bg(y + 0.5, y - 2.5, 'Phase 9: Cleanup + SaveConversation', '5 memory calls · ~600ms')
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× CreateEvent + 2× ListEvents + 1× CreateEvent', C_MEMORY)
y -= 1.5
arrow('AgentCore\nRuntime', 'AgentCore\nMemory', y, '1× ListEvents + 1× CreateEvent — SaveConversation', C_MEMORY)

# ============================================================
# Response to user
# ============================================================
y -= 2.0
arrow('AgentCore\nRuntime', 'User', y, 'Streamed response with Plan A/B/C details + enrollment info', C_USER, bold=True)

# ============================================================
# Summary box at bottom
# ============================================================
y -= 2.5
summary = (
    "TOTALS:  16.8s end-to-end  ·  2 LLM calls (12.5s, 78%)  ·  27 memory API calls (3.2s, 19%)  ·  "
    "1 KB search (1.1s)  ·  4,579 tokens (4,052 in + 527 out)"
)
ax.add_patch(mpatches.FancyBboxPatch((3, y - 1.2), 94, 2.2, boxstyle="round,pad=0.3",
                                      facecolor='#2C3E50', edgecolor='none', alpha=0.9))
ax.text(50, y, summary, ha='center', va='center', fontsize=8, color='white', fontweight='bold')

# Title
ax.text(50, 99.5, 'Agent Session Flow: "Tell me about the medical insurance options"',
        ha='center', va='center', fontsize=14, fontweight='bold', color='#2C3E50')

plt.tight_layout()
import os
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_sequence_diagram.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path}")
