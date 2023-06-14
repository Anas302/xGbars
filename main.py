from matplotlib.patches import Circle, Rectangle
import matplotlib.pyplot as plt

# Create a figure and axes
fig = plt.figure(figsize=(12, 6))
ax = plt.axes([0, 0, 1, 1], frameon=True)  # change frameon = False to remove box borders
ax.grid(False)
# ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.set_aspect("equal")
ax.autoscale(tight=True)

# circle = Circle((0, 0.75), radius=0.1, fc='yellow')
circle2 = Circle((9, 0.75), radius=0.1, fc='yellow')

# Create Patch objects
TOTAL_TIMELINE_WIDTH = 9  # 9 corresponds to 90 minutes
TIMELINE_HEIGHT = 0.05
XG_BAR_WIDTH = 0.1  # 1 minute for each expected goal bar
XG_BAR_HEIGHT = 0.2


def draw_xg_bar(minute, xG=0.0, isAway=False):
    assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"

    if isAway:
        # create the away xG bar
        away = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 - TIMELINE_HEIGHT / 2), width=XG_BAR_WIDTH,
                         height=-XG_BAR_HEIGHT, fc='red', alpha=0.5)

        if xG == 1:
            goal = Circle(xy=(minute + XG_BAR_WIDTH / 2, -(0.5 + XG_BAR_HEIGHT + 0.05)),
                          radius=0.1, fc='blue', alpha=0.5)
            ax.add_patch(goal)

        ax.add_patch(away)

    else:
        # create the home xG bar
        home = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 + TIMELINE_HEIGHT / 2), width=XG_BAR_WIDTH,
                         height=XG_BAR_HEIGHT, fc='blue', alpha=0.5)
        if xG == 1:
            goal = Circle(xy=(minute + XG_BAR_WIDTH / 2, 0.5 + XG_BAR_HEIGHT + 0.05),
                          radius=0.1, fc='blue', alpha=0.5)
            ax.add_patch(goal)
        ax.add_patch(home)

    timeline = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 - TIMELINE_HEIGHT / 2), width=XG_BAR_WIDTH,
                         height=TIMELINE_HEIGHT, fc='yellow', alpha=0.5)
    ax.add_patch(timeline)


draw_xg_bar(0, 0.5)

# Add Patch objects to the axes
# ax.add_patch(circle)
ax.add_patch(circle2)

# Set the aspect ratio to equal and adjust the limits
# ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Show the plot
plt.show()
