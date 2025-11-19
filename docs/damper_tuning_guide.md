# Damper Tuning Guide - ClaudeTunes Methodology

## The Core Concept: Damping Ratio

**What it controls**: How quickly suspension oscillations settle down after hitting bumps or cornering transitions.

**The sweet spot**: 0.65-0.70 damping ratio for racing
- Lower (0.25): Passenger car comfort - bouncy, slow to settle
- Higher (1.0): Critically damped - no overshoot but slower response
- Too high (>1.0): Overdamped - sluggish and poor grip

---

## Why Split Compression vs Rebound?

**Energy flow tells the story:**
- **Compression**: Energy goes INTO the spring (spring does some work)
- **Rebound**: Energy comes OUT of spring (damper must control it all)

**The ratio**: Rebound should be ~1.5× compression force
- Compression: 2/3 of baseline slope
- Rebound: 3/2 of baseline slope

---

## GT7 Damper Settings Translation

**Base compression**: 25% + modifiers  
**Base rebound**: 35% + modifiers

### Modifiers that increase damping:

#### 1. Drivetrain (body control needs):
- FF: +3% (weight transfer management)
- FR: +1% (balanced)
- MR: 0% (low CG, minimal body motion)
- RR: -2% (rear weight helps platform)
- AWD: +1% (stability)

#### 2. Power level (platform control):
- <400 HP: 0%
- 400-600 HP: +2%
- 600-700 HP: +6%
- >700 HP: +8%

#### 3. CG height (roll control):
- High: +2%
- Standard: 0%
- Low: -1%

#### 4. Track type (response needs):
- High-speed: +3% (stability)
- Technical: -2% (compliance)

---

## Real-World Example

**992 Turbo S (665 HP, RR, high CG, mixed track):**

**Compression**: 25% + 0% (RR drivetrain) + 6% (665 HP) + 2% (high CG) + 0% (mixed) = **33-35%**

**Rebound**: 35% + 0% + 6% + 2% + 0% = **43-45%**

---

## High-Speed vs Low-Speed Damping

**Low-speed** (0-2 in/sec):
- Controls body roll, dive, squat
- What you feel during cornering/braking
- Higher values here = better platform control

**High-speed** (>5 in/sec):
- Controls bump absorption
- Hitting curbs, surface irregularities
- Lower values here = better mechanical grip

**GT7 percentage settings** control the overall curve, with the game automatically managing the velocity-dependent behavior.

---

## The Transmissibility Insight

**Key physics**: At frequencies below your suspension's natural frequency (the ride frequency you calculated), you WANT more damping to reduce overshoot. But at high frequencies (bumps), you want LESS damping for better compliance.

This is why professional dampers use **high-speed rolloff** - cutting damping force in half at high shaft velocities.

GT7 approximates this through its percentage-based system, where the game's physics engine handles the velocity-dependent behavior behind the scenes.

---

## What Happens When It's Wrong?

### Too soft (under-damped):
- Car oscillates after bumps
- Floaty feeling
- Inconsistent platform
- Multiple bounces after kerbs

### Too stiff (over-damped):
- Harsh ride
- Poor mechanical grip
- Tires skip over bumps
- Slow weight transfer response

### Compression too high:
- Harsh bump response
- Reduced mechanical grip
- Car "packs down" on rough sections

### Rebound too high:
- Car won't settle after compression
- Wheels don't follow road surface
- "Pogo stick" effect

---

## The ClaudeTunes Approach

I calculate your baseline damping from:
1. Your suspension frequency (from tire compound + drivetrain)
2. Vehicle characteristics (power, CG, weight)
3. Track demands (high-speed vs technical)

Then adjust the compression/rebound split based on the energy flow principle.

**The beauty**: Once you have the right frequencies and ARB balance, dampers fine-tune the dynamic response without changing the fundamental balance.

---

## Professional OptimumG Formulas

### Baseline Damping Force Calculation:

**Initial Slope** = (4π × ζ × ω × m_sm) N/(m/s)

Where:
- ζ (zeta) = Damping ratio (0.65-0.70 for racing)
- ω (omega) = Ride frequency (Hz)
- m_sm = Sprung mass supported by damper (kg)

### Modified Compression/Rebound Split:

**Compression Slope** = 2/3 × Initial Slope  
**Rebound Slope** = 3/2 × Initial Slope

### High-Speed Rolloff:

**High-Speed Compression** = 1/3 × Initial Slope  
**High-Speed Rebound** = 3/4 × Initial Slope

---

## GT7 Conversion Quick Reference

| Parameter | Base % | FF | FR | MR | RR | AWD |
|-----------|--------|----|----|----|----|-----|
| **Compression** | 25% | +3% | +1% | 0% | -2% | +1% |
| **Rebound** | 35% | +3% | +1% | 0% | -2% | +1% |

**Additional Adjustments:**
- 400-600 HP: +2%
- 600-700 HP: +6%
- >700 HP: +8%
- High CG: +2%
- High-speed track: +3%
- Technical track: -2%

---

## Summary

Dampers are the "shock absorbers" that control how quickly your suspension responds to inputs. The ClaudeTunes methodology calculates physics-based damping ratios that:

1. **Control body motion** without sacrificing mechanical grip
2. **Separate compression/rebound** based on energy flow principles
3. **Adapt to vehicle characteristics** (power, weight, drivetrain)
4. **Optimize for track type** (high-speed stability vs technical compliance)

**Result**: Predictable, progressive handling that maximizes tire contact and driver confidence.

---

*Based on OptimumG professional race engineering principles and validated through ClaudeTunes GT7 success stories.*