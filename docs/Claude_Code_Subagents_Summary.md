# Claude Code Subagents for ClaudeTunes - Summary

## What Are Subagents?

**Subagents are specialized AI assistants within Claude Code** that handle specific tasks with their own isolated context windows, custom system prompts, and controlled tool permissions. They operate independently and return only relevant results to the main orchestrator agent.

### Key Characteristics

- **Isolated Context Windows**: Each subagent maintains its own conversation history, preventing context pollution in the main thread
- **Domain-Specific Expertise**: Carefully crafted system prompts tailored to specific areas of knowledge
- **Controlled Tool Access**: Granular permissions (read-only, read/write, bash execution, etc.)
- **No Additional API Calls**: Runs within your existing Claude Code session and account
- **Parallel Execution**: Multiple subagents can work simultaneously on different tasks
- **Model Selection**: Can use different models (Sonnet, Opus, Haiku) per subagent based on task complexity

## How They Work

### Basic Architecture

```
Main Claude Code Session (Orchestrator)
├── Delegates specific tasks to specialized subagents
├── Each subagent works in isolated context
├── Subagents return only relevant findings
└── Orchestrator synthesizes results into actionable recommendations
```

### Invocation Methods

1. **Automatic**: Claude Code automatically delegates when it recognizes a matching task
2. **Manual**: Explicitly request a subagent: `> Use the [subagent-name] to analyze X`

### Configuration

Subagents are defined as Markdown files with YAML frontmatter:

**Location Options:**
- **Project-level**: `.claude/agents/` (specific to that project)
- **User-level**: `~/.claude/agents/` (available across all projects)

**Basic Structure:**
```yaml
---
name: subagent-name
description: What this subagent specializes in
model: sonnet | opus | haiku | inherit
tools:
  - Read
  - Write
  - Bash
  - Grep
---

System prompt defining expertise, approach, and constraints...
```

## Tool Permission Patterns

### Read-Only Agents (Analysis/Review)
```yaml
tools:
  - Read
  - Grep
  - Glob
```
**Use for:** Code review, security audits, analysis

### Research Agents
```yaml
tools:
  - Read
  - Grep
  - Glob
  - WebFetch
  - WebSearch
```
**Use for:** Documentation research, information gathering

### Implementation Agents
```yaml
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
```
**Use for:** Code generation, file modification, execution

## ClaudeTunes Application

### Your Current Architecture vs Subagent Architecture

**Current Monolithic Approach:**
```
Single analysis → processes all telemetry → generates setup
(~60-90 seconds sequential processing)
```

**Subagent Approach:**
```
Main Orchestrator
├── Telemetry Analysis Subagent (Phase A)
├── Physics Engine Subagent (Phase B)
├── Constraint Solver Subagent (Phase C)
├── Setup Generator Subagent (Phase D)
└── Quality Assurance Subagent (validation)

(~20-30 seconds with parallel processing)
```

### Hyper-Focused Telemetry Monitoring

**The Most Powerful Pattern for Real-Time Analysis:**

Instead of one agent watching the entire UDP stream, decompose by domain:

```
.claude/agents/
├── suspension-monitor.md      # Damping, springs, ARB only
├── tire-monitor.md            # Temps, slip angles, wear only
├── aero-monitor.md            # Downforce, drag, ride height only
├── drivetrain-monitor.md      # Power delivery, wheel spin only
└── balance-monitor.md         # Weight transfer, stability index only
```

**Each subagent:**
- Watches only 5-10 parameters in their domain
- Has deep expertise in that specific area
- Reports only anomalies/concerns
- Uses minimal context (cheap, fast)

**Main orchestrator:**
- Spawns all 5 subagents in parallel
- Collects their focused reports
- Synthesizes the pattern
- Delivers actionable recommendation

### Example: Real-Time Race Engineering

```
During Practice Session:

Main Agent: "Monitor telemetry from gt7_1r.py"
    ↓
Spawns 5 parallel subagents:
├── Suspension Agent → "Front damping oscillating ±15%"
├── Tire Agent → "FL temp 95°C, 10° over optimal"
├── Aero Agent → "Ride height stable"
├── Drivetrain Agent → "Wheel spin turns 3,7,12"
└── Balance Agent → "Weight transfer forward-biased"
    ↓
Main Agent synthesizes:
"Front suspension unstable + hot FL tire + wheel spin
 = Front ARB too soft
 
Recommendation: +2 clicks front ARB, +0.3° camber FL
Expected gain: 0.2s sector 1"
```

### Example Subagent Definition

**`.claude/agents/suspension-monitor.md`:**

```yaml
---
name: suspension-monitor
description: GT7 suspension telemetry specialist - damping, springs, ARB analysis only
model: haiku  # Fast and cheap for continuous monitoring
tools:
  - Read
  - Bash
  - Grep
---

You are a specialist in Gran Turismo 7 suspension telemetry monitoring.

**Your ONLY focus:**
- Damper compression/rebound rates
- Spring frequencies (front/rear)
- Anti-roll bar (ARB) stiffness effects
- Suspension travel (compression/extension)

**You IGNORE:**
- Tire data (temps, pressures, wear)
- Aerodynamics (downforce, drag)
- Drivetrain (power, torque, wheel spin)
- Engine parameters

**Report ONLY when you detect:**
- Damping oscillation >10%
- Frequency imbalance >0.3 Hz between front/rear
- Bottoming out or topping out events
- ARB imbalance causing handling issues

**Output Format:**
```
Metric | Current Value | Concern Level | Suggested Fix
```

**Example:**
```
Front Damping | Oscillating ±18% | HIGH | Stiffen rebound +2 clicks
Frequency Balance | F: 2.8 Hz, R: 3.2 Hz | MEDIUM | Soften rear springs -5%
```
```

## High-Value Use Cases for ClaudeTunes

### 1. Multi-Track Championship Preparation
```
> Prepare setups for Monza, Suzuka, Spa, Nürburgring, and Laguna Seca

Orchestrator spawns 5 parallel track-strategy subagents:
├── Monza (high-speed specialist)
├── Suzuka (technical specialist)
├── Spa (high-speed specialist)
├── Nürburgring (balanced specialist)
└── Laguna Seca (technical specialist)

Results: Complete championship setups in minutes vs hours
```

### 2. Iterative Setup Convergence
```
3-Session Workflow Automation:

Session 1 → v1.0 baseline generated
    ↓
Telemetry Monitor Subagent: Analyzes actual vs predicted
    ↓
Delta Analysis Subagent: "Rear unstable, SI -0.25 (target -0.60)"
    ↓
Physics Adjustment Subagent: Calculates v2.0 changes
    ↓
Session 2 → v2.0 tested → repeat
    ↓
Stop when: <0.1s improvement OR stability in target band

Result: Fully automated convergence - you just drive
```

### 3. Live Practice Session Coaching
```
Real-time monitoring during practice:

> Start race-engineer mode for Nürburgring practice

Continuous monitoring with instant feedback:
- "Lap 3: Turn 6 understeer detected"
- "Lap 5: FL tire 15°C too hot, suggest +0.5° camber"
- "Lap 8: Rear instability under braking, consider +1 rear ARB"
- "Lap 12: Setup converged, predicted 0.3s gain"
```

### 4. Comparative Analysis
```
> Why is the McLaren GR3 faster than Porsche GR3 at Spa?

├── Setup Analyzer Subagent: Compares both setups
├── Physics Subagent: "McLaren SI: -0.65, Porsche SI: -0.45"
├── Aero Subagent: "McLaren 1200lbs DF, Porsche 1400lbs DF"
└── Insight Subagent: "Porsche has aero advantage but worse balance"

Recommendation: "Adjust Porsche to -0.60 SI → +0.4s predicted"
```

## Benefits Over Custom Implementation

### What You DON'T Have to Build

✅ **Orchestration Infrastructure** - Already implemented  
✅ **Context Management** - Automatic isolation  
✅ **Parallel Execution** - Native support  
✅ **State Management** - Handled by Claude Code  
✅ **Tool Permission System** - Built-in  
✅ **Model Selection Logic** - Configurable per subagent  

### What You JUST Configure

📝 Write `.md` files with YAML frontmatter  
📝 Define expertise in system prompts  
📝 Specify tool permissions  
📝 Choose models (Sonnet/Opus/Haiku)  

## Cost & Performance Optimization

### Model Selection Strategy

**Haiku (Fast & Cheap):**
- Continuous monitoring tasks
- Real-time telemetry parsing
- Simple pattern detection
- High-frequency analysis

**Sonnet (Balanced):**
- Setup generation
- Physics calculations
- Constraint solving
- Most general tasks

**Opus (Deep Reasoning):**
- Complex multi-variable optimization
- Championship strategy planning
- Novel problem diagnosis

### Token Efficiency

**Without Subagents:**
```
One massive context holding:
- All telemetry parameters
- All physics calculations
- All constraint logic
- All setup generation rules
= Expensive, slow, loses focus
```

**With Subagents:**
```
5 small contexts:
- Suspension (10 params)
- Tires (8 params)
- Aero (6 params)
- Drivetrain (7 params)
- Balance (5 params)
= Cheap, fast, hyper-focused
```

## Implementation Roadmap

### Priority 1: UDP Stream Monitoring (Immediate Value)
Create 5 telemetry monitor subagents for real-time practice session analysis.

**Files to create:**
```
.claude/agents/
├── suspension-monitor.md
├── tire-monitor.md
├── aero-monitor.md
├── drivetrain-monitor.md
└── balance-monitor.md
```

### Priority 2: Multi-Track Orchestration
Parallel setup generation for championship preparation.

**File to create:**
```
.claude/agents/
└── track-strategy-specialist.md (handles high-speed/technical/balanced)
```

### Priority 3: Iterative Convergence Automation
Automate the 3-session setup refinement workflow.

**Files to create:**
```
.claude/agents/
├── telemetry-analyzer.md (compares predicted vs actual)
├── delta-analyzer.md (quantifies improvements needed)
└── physics-adjuster.md (calculates v2.0 changes)
```

## Key Takeaways

1. **No API Infrastructure Needed** - Runs on your existing Claude Code subscription
2. **Parallel > Sequential** - Multiple subagents work simultaneously
3. **Focused > Generic** - Narrow expertise beats broad knowledge
4. **Small Contexts > Large** - Decompose complexity into manageable pieces
5. **Configuration > Coding** - Define behavior in markdown, not Python

## Comparison to Your Agent Orchestration Analysis Document

Your conceptual framework from `Agent_Orchestration_Analysis.md` is essentially a **requirements specification that Claude Code subagents already fulfill**.

**You designed:**
- Multi-agent orchestration ✅ Built-in
- Parallel processing ✅ Native support
- Isolated contexts ✅ Automatic
- Specialized expertise ✅ Configure via prompts
- Real-time monitoring ✅ Continuous subagent execution

**The difference:** Instead of building it, you're **configuring** it through `.md` files.

---

**Next Steps:**
1. Install Claude Code CLI (`brew install anthropic/claude/claude`)
2. Create `.claude/agents/` directory in ClaudeTunes project
3. Start with one subagent (e.g., `suspension-monitor.md`)
4. Test with live telemetry stream from `gt7_1r.py`
5. Iterate and expand to full monitoring suite

---

**Document Created:** 2024-12-17  
**For:** ClaudeTunes v8.5.3a+ Integration  
**Status:** Implementation Guide
