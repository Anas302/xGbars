from matplotlib.patches import Circle, Rectangle
import matplotlib.pyplot as plt

# Create a figure and axes
fig = plt.figure(figsize=(12, 6), dpi=200)
ax = plt.axes([0, 0, 1, 1], frameon=True)  # change frameon = False to remove box borders
ax.grid(False)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.set_aspect("equal")
ax.autoscale(tight=True)


# Create Patch objects
TOTAL_TIMELINE_WIDTH = 9  # 9 units corresponds to 90 minutes
XG_BAR_WIDTH = 0.1  # 0.1 unit corresponds to 1 minute for each expected goal bar
timeline_color = '#892828'
timeline_height = 0.05
xg_bar_height = 0.2


def draw_xg_bar(minute: int, xG: float = 0.0, isAway: bool = False, color: str = "#000000"):
    """
    Draw an xG bar along the timeline axis. If the xG was 1 a circle will also be drawn on the bar to indicate a goal.
    Away team is plotted under the timeline while the home team is plotted over it. The color is by default set to black
    :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
    :param xG: the expected goal score during this minute of play.
    :param isAway: whether the xG belongs to the away team or the home team.
    :param color:
    :return:
    """
    assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"
    assert 0 <= minute <= 90, "The time minute must be between 0 and 90 inclusive"
    minute /= 10

    if xG != 0:
        if isAway:
            # create the away xG bar
            away = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 - timeline_height / 2), width=XG_BAR_WIDTH,
                             height=-xg_bar_height, fc=color)

            if xG == 1:
                goal = Circle(xy=(minute + XG_BAR_WIDTH + XG_BAR_WIDTH/2, 0.5 - xg_bar_height - 0.05),
                              radius=0.1, fc=color)
                ax.add_patch(goal)

            ax.add_patch(away)

        else:
            # create the home xG bar
            home = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 + timeline_height / 2), width=XG_BAR_WIDTH,
                             height=xg_bar_height, fc=color)
            if xG == 1:
                goal = Circle(xy=(minute + XG_BAR_WIDTH + XG_BAR_WIDTH/2, 0.5 + xg_bar_height + 0.05),
                              radius=0.1, fc=color)
                ax.add_patch(goal)
            ax.add_patch(home)

    timeline = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 - timeline_height / 2), width=XG_BAR_WIDTH,
                         height=timeline_height, fc=timeline_color)
    ax.add_patch(timeline)


draw_xg_bar(0, 1)
draw_xg_bar(45, 1, False, color='#1B398A')
draw_xg_bar(25, 0, True)
draw_xg_bar(90, 1, True)

# Set the aspect ratio to equal and adjust the limits
# ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Show the plot
plt.show()
