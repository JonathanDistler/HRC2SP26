import matplotlib.pyplot as plt

# INPUT PLAN, will be provided by Timothy after LLM communication phase
plan = """(move p2 kitchen pantry)
(take p2 ham pantry)
(move p2 pantry kitchen)
(move p1 kitchen pantry)
(take p1 bread pantry)
(move p1 pantry kitchen)
(slice-ham p2 kitchen ham)
(drop p2 ham kitchen)
(take p2 lettuce kitchen)
(wash-lettuce p2 kitchen lettuce)
(drop p2 lettuce kitchen)
(drop p1 bread kitchen)
(make-sandwich p2 kitchen bread cheese ham lettuce)
"""

# Parse: strips all of them from () and determines verb (or action), agent, and locations
def parse_plan(plan):
    return [line.strip()[1:-1] for line in plan.splitlines() if line.strip()]

def split_action(action):
    parts = action.split()
    return {
        "verb": parts[0],
        "agent": parts[1],
        "args": parts[2:]
    }

actions = [split_action(a) for a in parse_plan(plan)]

# INITIAL STATE: provided by the domain.pddl, can change from time to time given constraints of problem 
state_init = {
    ("at", "p1", "kitchen"),
    ("at", "p2", "kitchen"),
    ("empty-hand", "p1"),
    ("empty-hand", "p2"),
    ("in-room", "bread", "pantry"),
    ("in-room", "ham", "pantry"),
    ("in-room", "cheese", "kitchen"),
    ("in-room", "lettuce", "kitchen"),
    ("knife-board-present", "kitchen"),
    ("sink-present", "kitchen"),
}

# ACTION SEMANTICS: determines preconditions that need to be met 
def get_preconditions(a):
    v = a["verb"]
    ag = a["agent"]
    args = a["args"]

    if v == "move":
        return {("at", ag, args[0])}

    if v == "take":
        return {
            ("at", ag, args[1]),
            ("in-room", args[0], args[1]),
            ("empty-hand", ag)
        }

    if v == "drop":
        return {
            ("holding", ag, args[0]),
            ("at", ag, args[1])
        }

    if v == "slice-ham":
        return {
            ("in-room", "ham", args[0]),
            ("knife-board-present", args[0])
        }

    if v == "wash-lettuce":
        return {
            ("in-room", "lettuce", args[0]),
            ("sink-present", args[0])
        }

    if v == "make-sandwich":
        return {
            ("in-room", "bread", "kitchen"),
            ("in-room", "ham", "kitchen"),
            ("in-room", "cheese", "kitchen"),
            ("in-room", "lettuce", "kitchen"),
            ("sliced", "ham"),
            ("washed", "lettuce")
        }

    return set()

#determines how an action affects the state 
def apply_effects(state, a):
    v = a["verb"]
    ag = a["agent"]
    args = a["args"]

    state = set(state)

    if v == "move":
        state.discard(("at", ag, args[0]))
        state.add(("at", ag, args[1]))

    elif v == "take":
        state.discard(("in-room", args[0], args[1]))
        state.discard(("empty-hand", ag))
        state.add(("holding", ag, args[0]))

    elif v == "drop":
        state.discard(("holding", ag, args[0]))
        state.add(("in-room", args[0], args[1]))
        state.add(("empty-hand", ag))

    elif v == "slice-ham":
        state.add(("sliced", "ham"))

    elif v == "wash-lettuce":
        state.add(("washed", "lettuce"))

    elif v == "make-sandwich":
        state.add(("sandwich-made",))

    return state

# PLAN REPAIR: pddl output isn't sequential, this makes it sequential based on preconditions that need to be met 
def repair_plan(actions):
    remaining = actions[:]
    ordered = []
    state = set(state_init)

    while remaining:
        progress = False

        for act in remaining[:]:
            if get_preconditions(act).issubset(state):
                state = apply_effects(state, act)
                ordered.append(act)
                remaining.remove(act)
                progress = True

        if not progress:
            raise Exception("Plan cannot be repaired") #e.g. no logical sequence follows, could be an issue for "lactose intolerant" case

    return ordered


actions = repair_plan(actions)

# EFFECT CACHE: determines how state changes 
effects_cache = []
tmp_state = set(state_init)

for act in actions:
    before = set(tmp_state)
    tmp_state = apply_effects(tmp_state, act)
    effects_cache.append(tmp_state - before)

# DEPENDENCIES
def build_dependencies(actions):
    deps = {i: set() for i in range(len(actions))}

    for i, act in enumerate(actions):
        for p in get_preconditions(act):
            for j in range(i - 1, -1, -1):
                if p in effects_cache[j]:
                    deps[i].add(j)
                    break

    return deps


deps = build_dependencies(actions)

# SCHEDULING (1 ACTION / AGENT / STEP): helps build order on how things progress 
BUFFER = 1
times = {}
agent_next_free = {"p1": 0, "p2": 0}

for i in range(len(actions)):
    act = actions[i]
    agent = act["agent"]

    if not deps[i]:
        dep_time = 0
    else:
        dep_time = max(times[d] for d in deps[i]) + BUFFER

    t = max(dep_time, agent_next_free[agent])

    times[i] = t
    agent_next_free[agent] = t + 1

# normalize
min_time = min(times.values())
times = {k: v - min_time + 1 for k, v in times.items()}

# TIMELINE: step by step action walk through with concurrent tasks parallel and dependent tasks buffered with a line connecting
timeline_dict = {}
for i, t in times.items():
    timeline_dict.setdefault(t, []).append(i)

timeline = [timeline_dict[t] for t in sorted(timeline_dict)]

# LABELS for the graph 
def build_label(act):
    v = act["verb"]
    args = act["args"]

    if v == "move":
        return f"move\n{args[0]} → {args[1]}"
    elif v == "take":
        return f"take {args[0]}"
    elif v == "drop":
        return f"drop {args[0]}"
    elif v == "slice-ham":
        return "slice ham"
    elif v == "wash-lettuce":
        return "wash lettuce"
    elif v == "make-sandwich":
        return "make sandwich"
    return v

# PLOT via matplotlib to make a quick and easy visual for human agent
fig, ax = plt.subplots(figsize=(20, 8))

agent_y = {"p1": 1, "p2": -1}
positions = {}

for t, step in enumerate(timeline, start=1):
    for idx in step:
        act = actions[idx]
        x = t
        y = agent_y[act["agent"]]

        positions[idx] = (x, y)

        color = "lightblue" if act["agent"] == "p1" else "lightgreen"

        ax.text(
    x, y,
    build_label(act),
    ha='center',
    va='center',
    bbox=dict(
        boxstyle="round,pad=0.5",
        fc=color,
        ec="black"
    )
)

# DRAW EDGES
for j in range(len(actions)):
    for i in deps[j]:
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        ax.plot([x1, x2], [y1, y2], 'black')

# FORMAT
ax.set_yticks([agent_y["p2"], agent_y["p1"]])
ax.set_yticklabels(["Agent p2", "Agent p1"])
ax.set_xticks(range(1, len(timeline) + 1))
ax.set_xlabel("Time Step")
ax.set_title("Parallel Plan (1 Action per Agent per Step)")

ax.set_ylim(-2, 2)
ax.grid(True)

plt.show()