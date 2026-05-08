import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from collections import defaultdict

# =========================================================
# PLAN
# =========================================================
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

# =========================================================
# PARSE
# =========================================================
def parse_plan(plan):
    return [
        line.strip()[1:-1]
        for line in plan.splitlines()
        if line.strip()
    ]

def split_action(action):

    p = action.split()

    return {
        "verb": p[0],
        "agent": p[1] if len(p) > 1 else "unknown",
        "args": p[2:],
        "raw": action
    }

actions = [split_action(a) for a in parse_plan(plan)]

# =========================================================
# FINAL INGREDIENTS
# =========================================================
#
# Extract ingredients from final assembly action.
# Robust to different task names.
#
final_action = actions[-1]

KNOWN_LOCATIONS = {
    "kitchen",
    "pantry",
    "table",
    "counter",
    "sink",
    "fridge",
    "cabinet"
}

ingredients = [
    a for a in final_action["args"]
    if a.lower() not in KNOWN_LOCATIONS
]

# =========================================================
# HELPERS
# =========================================================
def normalize(text):
    return text.lower()

def belongs_to(act, ingredient):

    ingredient = normalize(ingredient)

    return (
        ingredient in [normalize(a) for a in act["args"]]
        or ingredient in normalize(act["verb"])
    )

def ingredient_from_action(act):

    for ing in ingredients:
        if belongs_to(act, ing):
            return ing

    return None

def is_move(act):
    return act["verb"] == "move"

# =========================================================
# COLUMN ORGANIZATION
# =========================================================
#
# Key idea:
#
# Movement actions belong ONLY to:
# - the NEXT action performed
# - by the SAME AGENT
#
# This avoids:
# - human moves appearing in ham
# - robot moves appearing in bread
#
# Robust for arbitrary PDDL outputs.
#
# =========================================================

columns = defaultdict(list)

# Track move per agent
pending_move = {}

for act in actions[:-1]:

    agent = act["agent"]

    # -----------------------------------------------------
    # STORE MOVEMENT TEMPORARILY
    # -----------------------------------------------------
    if is_move(act):

        pending_move[agent] = act
        continue

    # -----------------------------------------------------
    # FIND INGREDIENT COLUMN
    # -----------------------------------------------------
    ing = ingredient_from_action(act)

    if ing is None:
        continue

    col_name = ing.upper()

    # -----------------------------------------------------
    # ATTACH AGENT'S PENDING MOVE
    # -----------------------------------------------------
    if agent in pending_move:

        move_act = pending_move[agent]

        columns[col_name].append(move_act)

        del pending_move[agent]

    # -----------------------------------------------------
    # ADD CURRENT ACTION
    # -----------------------------------------------------
    columns[col_name].append(act)

# =========================================================
# ENSURE ALL INGREDIENTS EXIST
# =========================================================
for ing in ingredients:

    col_name = ing.upper()

    if col_name not in columns:

        columns[col_name] = []

# =========================================================
# ADD UNASSIGNED BLOCKS
# =========================================================
for col_name in columns:

    if len(columns[col_name]) == 0:

        columns[col_name].append({
            "verb": "unassigned",
            "agent": "unknown",
            "args": [],
            "raw": f"unassigned-{col_name}"
        })

# =========================================================
# CROSS-AGENT DEPENDENCIES
# =========================================================
#
# Dashed arrows ONLY when:
# - one agent finishes with ingredient
# - another agent later uses ingredient
#
# Example:
# Human drops bread
# Robot assembles bread
#
# =========================================================

dependency_arrows = []

for ing in ingredients:

    relevant = []

    for act in actions:

        if belongs_to(act, ing):
            relevant.append(act)

    for i in range(len(relevant) - 1):

        a1 = relevant[i]
        a2 = relevant[i + 1]

        if a1["agent"] != a2["agent"]:

            dependency_arrows.append((a1, a2))

# =========================================================
# AGENT COLORS
# =========================================================
AGENT_MAP = {
    "p1": "human",
    "p2": "robot",
    "human": "human",
    "robot": "robot",
    "system": "unassigned",
    "unknown": "unassigned"
}

COLORS = {
    "human": "#2e7d32",
    "robot": "#1565c0",
    "unassigned": "#616161"
}

def normalize_agent(agent):
    return AGENT_MAP.get(agent.lower(), "unassigned")

def get_color(agent):
    return COLORS[normalize_agent(agent)]

def agent_label(agent):
    return normalize_agent(agent).capitalize()

# =========================================================
# NATURAL LANGUAGE LABELS
# =========================================================
def to_natural(act):

    verb = act["verb"]
    agent = agent_label(act["agent"])

    obj = ingredient_from_action(act)

    # -----------------------------------------------------
    # UNASSIGNED
    # -----------------------------------------------------
    if verb == "unassigned":
        return "Unassigned\n(No actions)"

    # -----------------------------------------------------
    # MOVE
    # -----------------------------------------------------
    if verb == "move":

        src = act["args"][0]
        dst = act["args"][1]

        return f"Move\n{src} → {dst}\n({agent})"

    # -----------------------------------------------------
    # TAKE
    # -----------------------------------------------------
    if verb == "take":
        return f"Pick up {obj}\n({agent})"

    # -----------------------------------------------------
    # DROP
    # -----------------------------------------------------
    if verb == "drop":
        return f"Drop {obj}\n({agent})"

    # -----------------------------------------------------
    # PROCESSING
    # -----------------------------------------------------
    if "slice" in verb:
        return f"Slice {obj}\n({agent})"

    if "wash" in verb:
        return f"Wash {obj}\n({agent})"

    if "cook" in verb:
        return f"Cook {obj}\n({agent})"

    if "toast" in verb:
        return f"Toast {obj}\n({agent})"

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------
    return f"{verb.replace('-', ' ').title()}\n({agent})"

# =========================================================
# DRAW BOX
# =========================================================
def draw_box(ax, x, y, text, agent, w=1.35, h=0.45):

    color = get_color(agent)

    ax.add_patch(Rectangle(
        (x - w / 2, y - h / 2),
        w,
        h,
        facecolor=color,
        edgecolor="black",
        linewidth=1.2
    ))

    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=7,
        color="white"
    )

# =========================================================
# PLOT
# =========================================================
fig, ax = plt.subplots(figsize=(16, 10))

col_names = list(columns.keys())
col_x = [i * 2.0 for i in range(len(col_names))]

# =========================================================
# TITLE
# =========================================================
ax.text(
    sum(col_x) / len(col_x),
    7.8,
    "Task Plan Overview",
    ha="center",
    fontsize=14,
    bbox=dict(fc="#444", ec="none"),
    color="white"
)

# =========================================================
# DRAW COLUMNS
# =========================================================
lowest_y = 10

box_positions = {}

for x, name in zip(col_x, col_names):

    ax.text(
        x,
        7.0,
        name,
        ha="center",
        fontsize=11,
        fontweight="bold"
    )

    tasks = columns[name]

    for i, act in enumerate(tasks):

        y = 6.2 - i * 0.72

        lowest_y = min(lowest_y, y)

        draw_box(
            ax,
            x,
            y,
            to_natural(act),
            act["agent"]
        )

        box_positions[act["raw"]] = (x, y)

# =========================================================
# DEPENDENCY ARROWS
# =========================================================
for a1, a2 in dependency_arrows:

    if (
        a1["raw"] in box_positions
        and a2["raw"] in box_positions
    ):

        x1, y1 = box_positions[a1["raw"]]
        x2, y2 = box_positions[a2["raw"]]

        ax.annotate(
            "",
            xy=(x2, y2 + 0.22),
            xytext=(x1, y1 - 0.22),
            arrowprops=dict(
                arrowstyle="->",
                linestyle="dashed",
                color="gray",
                linewidth=1.2
            )
        )

# =========================================================
# ASSEMBLY
# =========================================================
assembly_y = lowest_y - 1.4
center_x = sum(col_x) / len(col_x)

draw_box(
    ax,
    center_x,
    assembly_y,
    "Assemble Final Product\n(Robot)",
    "p2",
    w=1.9
)

# =========================================================
# CONVERGENCE LINES
# =========================================================
for x in col_x:

    ax.plot(
        [x, center_x],
        [lowest_y - 0.25, assembly_y + 0.25],
        linestyle="dashed",
        color="gray",
        linewidth=0.9
    )

# =========================================================
# DELIVERY
# =========================================================
delivery_y = assembly_y - 1.1

draw_box(
    ax,
    center_x,
    delivery_y,
    "Deliver Task\n(Unassigned)",
    "unknown",
    w=1.8
)

# =========================================================
# LEGEND
# =========================================================
legend_x = col_x[-1] + 2.5

ax.text(
    legend_x,
    6.2,
    "Human",
    bbox=dict(fc=COLORS["human"]),
    color="white"
)

ax.text(
    legend_x,
    5.7,
    "Robot",
    bbox=dict(fc=COLORS["robot"]),
    color="white"
)

ax.text(
    legend_x,
    5.2,
    "Unassigned",
    bbox=dict(fc=COLORS["unassigned"]),
    color="white"
)

ax.text(
    legend_x,
    4.4,
    "Dashed arrows = cross-agent dependency",
    fontsize=8
)

# =========================================================
# CLEANUP
# =========================================================
ax.set_xlim(-1, legend_x + 2)
ax.set_ylim(delivery_y - 1, 8.2)

ax.axis("off")

plt.tight_layout()
plt.show()