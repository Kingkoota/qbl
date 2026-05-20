# Chapter 11: Agentic Constructs

## 11.1 Overview

QBL extends beyond static circuit descriptions into autonomous agent execution. The agentic layer enables quantum programs to be self-directing: agents sense, plan, act, and adapt using quantum resources as both computational substrate and communication medium.

**Key insight:** An agent's "reasoning" can exist in superposition until a measurement forces a classical decision. This provides genuine quantum advantage in strategy selection, consensus, and search.

## 11.2 Agent Declaration

```qbl
agent <Name> <<dimension>> {
    memory: <slots> slots
    tools: [<tool_list>]
    strategy: <initial_strategy>
    
    goal <goal_name> {
        metric: "<quantum_metric>"
        condition: <classical_condition>
        max_attempts: <int>
        priority: <int>
    }
}
```

### 11.2.1 Example

```qbl
agent Oracle<13> {
    memory: 8 slots
    tools: [quantum_sense, entangle, build_circuit, reason, correct]
    strategy: explore
    
    goal find_ground_state {
        metric: "energy < 0.1"
        max_attempts: 100
        priority: 10
    }
    
    goal maintain_coherence {
        metric: "fidelity > 0.99"
        max_attempts: unlimited
        priority: 5
    }
}
```

## 11.3 Agent Memory Model

Agent memory is quantum: linear, no-clone, error-corrected.

```qbl
// Store quantum state (move semantics — source consumed)
agent.store(slot: "workspace", state: prepared_qudit)

// Retrieve (consumes slot)
let state = agent.retrieve(slot: "workspace")

// Non-destructive fidelity check (weak measurement)
let f = agent.peek_fidelity(slot: "workspace", reference: |7⟩)

// Mark entangled
agent.entangle_slot("channel", partner: Bob, slot: "channel")
```

**Memory properties:**
| Property | Behavior |
|----------|----------|
| Store | Move semantics (no copy) |
| Retrieve | Consumes slot (linear type) |
| Peek | Weak measurement (minimal disturbance) |
| Entangled | Correlated with partner's memory |
| Corrected | Autonomous QEC on stored states |

## 11.4 Execution Loop

Every agent follows the **Sense → Plan → Act → Adapt** cycle:

```
┌─────────────────────────────────────────────┐
│                AGENT STEP                    │
│                                             │
│  ┌─────┐   ┌──────┐   ┌─────┐   ┌───────┐ │
│  │SENSE│──▶│ PLAN │──▶│ ACT │──▶│ ADAPT │ │
│  └─────┘   └──────┘   └─────┘   └───────┘ │
│      │                               │      │
│      └───────────────────────────────┘      │
│                  (feedback)                  │
└─────────────────────────────────────────────┘
```

### 11.4.1 Sense

```qbl
behavior Agent {
    on sense {
        obs.memory = quantum_sense(memory, observable: "coherence")
        obs.messages = check_inbox()
        obs.goals = evaluate_goals()
    }
}
```

### 11.4.2 Plan (Quantum-Enhanced)

```qbl
behavior Agent {
    on plan(observations) {
        // Strategy selection via quantum superposition
        qudit<4> strategy_register[1]  // 4 strategies: d=4 subsystem
        QFT(strategy_register[0])      // Uniform superposition of strategies
        
        // Oracle marks good strategies based on observations
        oracle(strategy_register, observations)
        
        // Grover amplification (√N speedup)
        amplify(strategy_register, iterations: 1)
        
        // Collapse to decision
        chosen = measure(strategy_register[0])
        // Result: {0: explore, 1: exploit, 2: communicate, 3: correct}
    }
}
```

### 11.4.3 Act

```qbl
behavior Agent {
    on act(strategy) {
        circuit = build_circuit(strategy, dimension: 13)
        result = execute(circuit)
        
        if result.success {
            store_result(result)
        }
    }
}
```

### 11.4.4 Adapt

```qbl
behavior Agent {
    on adapt(result) {
        // Bayesian belief update
        beliefs = reason(prior: beliefs, evidence: result)
        
        // Adjust exploration rate
        if result.success {
            exploration_rate *= 0.99  // More exploitation
        } else {
            exploration_rate *= 1.01  // More exploration
        }
    }
}
```

## 11.5 Multi-Agent Swarm

```qbl
swarm <Name> <<dimension>> {
    agents: [<agent_list>]
    topology: <topology>
    consensus: <protocol>
}
```

### 11.5.1 Topologies

| Topology | Description | Entanglement Cost |
|----------|-------------|-------------------|
| `all_to_all` | Every pair entangled | O(n²) Bell pairs |
| `ring` | Circular chain | O(n) Bell pairs |
| `star` | One central, all connect to it | O(n) Bell pairs |
| `tree` | Hierarchical | O(n) Bell pairs |
| `custom` | User-defined graph | Varies |

### 11.5.2 Swarm Declaration

```qbl
swarm Research_Team<13> {
    agents: [Explorer, Verifier, Coordinator, Optimizer]
    topology: star(center: Coordinator)
    consensus: quantum_majority
    
    on convergence {
        export results
        broadcast achievement
    }
}
```

## 11.6 Entangled Communication

Agents communicate via pre-shared entanglement — enabling:
- Instant correlation (no classical speed-of-light delay for correlation)
- Secure communication (eavesdropping detectable)
- Superdense coding (d² messages per d-level qudit sent)
- Teleportation (transfer unknown states)

```qbl
// Establish channel
channel Alice <-> Bob {
    type: bell_pair<13>
    protocol: teleportation
    error_correction: true
}

// Send quantum state via teleportation
Alice.send(state: prepared_qudit, to: Bob, via: teleportation)

// Superdense: encode d²=169 messages per transmission
Alice.encode(message: (7, 11), channel: entangled_qudit)
Alice.transmit(to: Bob)
result = Bob.decode()  // → (7, 11)

// Classical broadcast
Coordinator.broadcast(data: {"phase": "exploit"}, to: all)
```

## 11.7 Quantum Consensus

```qbl
consensus <name> {
    participants: <swarm_or_list>
    options: [<option_list>]
    method: quantum_majority | quantum_grover | quantum_vote
    threshold: <float>  // required agreement strength
}
```

### 11.7.1 Protocol

1. Each agent prepares their vote in the computational basis
2. Votes are entangled via multi-party GHZ state
3. Correlated measurements produce consensus faster than classical polling
4. For k options: O(√k) rounds to consensus vs O(k) classically

### 11.7.2 Example

```qbl
consensus decide_action {
    participants: Research_Team
    options: ["explore_new_region", "optimize_current", "divide_and_conquer"]
    method: quantum_majority
    threshold: 0.6
    
    on success(winner) {
        all_agents.set_strategy(winner)
    }
    
    on failure {
        // No consensus — agents keep individual strategies
        log("Consensus not reached, maintaining diversity")
    }
}
```

## 11.8 Tools

Agents access capabilities through a tool interface:

```qbl
// Built-in tools
tool quantum_sense {
    input: (state, observable)
    output: {value, uncertainty}
    destructive: false  // weak measurement
}

tool entangle {
    input: (dimension)
    output: (bell_pair, metadata)
    cost: 1 Bell pair
}

tool build_circuit {
    input: (strategy, dimension, num_qudits)
    output: circuit_plan
}

tool reason {
    input: (prior, evidence)
    output: posterior
    method: bayesian_update
}

// Custom tool registration
tool my_oracle {
    input: (state, target)
    output: {found: bool, confidence: float}
    implementation: "src/custom_oracle.qbl"
}
```

## 11.9 Autonomous Error Correction (Agentic)

Agents self-correct without external intervention:

```qbl
behavior Agent {
    on error_detected(syndrome) {
        correction = decode(syndrome, code: repetition_13)
        apply(correction)
        log("Self-corrected", syndrome: syndrome)
    }
    
    // Periodic maintenance
    every 5 steps {
        for slot in memory.occupied {
            fidelity = peek_fidelity(slot)
            if fidelity < 0.95 {
                correct(slot, code: repetition_13)
            }
        }
    }
}
```

## 11.10 Goal Hierarchy

Agents pursue goals with priority ordering:

```qbl
agent Researcher<13> {
    // High priority: maintain quantum coherence (always active)
    goal maintain_coherence {
        metric: "all memory slots fidelity > 0.99"
        priority: 100
        type: persistent  // Never completes
    }
    
    // Medium: find ground state
    goal find_ground_state {
        metric: "energy < 0.01"
        priority: 50
        max_attempts: 200
    }
    
    // Low: report results
    goal report {
        condition: find_ground_state.achieved
        priority: 10
        action: broadcast(result)
    }
}
```

## 11.11 Advantages of Quantum Agents

| Capability | Classical Agent | Quantum Agent (d=13) | Advantage |
|-----------|----------------|---------------------|-----------|
| Strategy search | O(k) | O(√k) | Grover speedup |
| Memory capacity | n bits per slot | n × 3.7 bits (superposition) | Exponential in superposition |
| Communication | 1 message/send | 169 messages/qudit | d² superdense |
| Consensus | O(n) rounds | O(√n) rounds | Quadratic speedup |
| Error correction | Redundancy | Stabilizer codes | Handles quantum noise |
| Exploration | Random walk | Quantum walk | Quadratic speedup |
| Security | RSA/AES | QKD (provable) | Information-theoretic |
