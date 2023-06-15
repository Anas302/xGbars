from matplotlib.patches import Circle, Rectangle
import matplotlib.pyplot as plt
import pandas as pd

# TODO:
#   - More interpolation techniques in the coloring scheme.
#   - Add bar height as a measure for xG as well.
#   - xG score can still result in a goal and be less than 1

# Create a figure and axes
fig = plt.figure(figsize=(12, 6), dpi=200)
ax = plt.axes([0, 0, 1, 1], frameon=False)  # change frameon = False to remove box borders
ax.grid(False)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.set_aspect("equal")
ax.autoscale(tight=True)

# Create Patch objects
MATCH_TIME = 120  # typical match lasts around 90 minutes
TOTAL_TIMELINE_WIDTH = MATCH_TIME/10
XG_BAR_WIDTH = 0.1  # 0.1 unit corresponds to 1 minute for each expected goal bar
timeline_color = (0.0, 0.0, 0.0)
timeline_height = 0.05
xg_bar_height = 0.75


def draw_xg_bar(minute: int, xG: float = 0.0, isAway: bool = False, color=(0.0, 0.0, 0.0)):
    """
    Draw an xG bar along the timeline axis. If the xG was 1 a circle will also be drawn on the bar to indicate a goal.
    Away team is plotted under the timeline while the home team is plotted over it. The color is by default set to black
    :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
    :param xG: the expected goal score during this minute of play.
    :param isAway: whether the xG belongs to the away team or the home team.
    :param color: RGB values between 0 and 1 in a 3D Tuple representing the color of the xG bar.
    """
    minute /= 10

    if xG != 0:
        if isAway:
            # create the away xG bar
            away = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 - timeline_height / 2), width=XG_BAR_WIDTH,
                             height=-xg_bar_height, fc=color)

            if xG == 1:
                goal = Circle(xy=(minute + XG_BAR_WIDTH + XG_BAR_WIDTH / 2, 0.5 - xg_bar_height - 0.05),
                              radius=XG_BAR_WIDTH + xg_bar_height/10, fc=color)
                ax.add_patch(goal)

            ax.add_patch(away)

        else:
            # create the home xG bar
            home = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 + timeline_height / 2), width=XG_BAR_WIDTH,
                             height=xg_bar_height, fc=color)
            if xG == 1:
                goal = Circle(xy=(minute + XG_BAR_WIDTH + XG_BAR_WIDTH / 2, 0.5 + xg_bar_height + 0.05),
                              radius=XG_BAR_WIDTH + xg_bar_height/10, fc=color)
                ax.add_patch(goal)
            ax.add_patch(home)

    timeline = Rectangle(xy=(minute + XG_BAR_WIDTH, 0.5 - timeline_height / 2), width=XG_BAR_WIDTH,
                         height=timeline_height, fc=timeline_color)
    ax.add_patch(timeline)


def get_rgb_from_xg(xG):
    """
    Given an xG score, return a color that correponds to it. The higher the xG the darker the color. By default the
    color uses linear interpolation, where xG = 1 is black and xG = 0 is white.
    :param xG: the expected goal score between [0, 1].
    :return: 3D Tuple represnting the RGB colors.
    """

    # Calculate interpolated color values
    red = 1 - xG
    green = 1 - xG
    blue = 1 - xG

    return red, green, blue


def xG_bars(xG_scores):
    """
    Draw the xG Bars from the given xG scores list along a 90-minute match.
    :param xG_scores: A list of 3D Tuples of the form (minute, xG, isAway),
    where 'minute' is the time of when the xG is recorded and must be an integer between 0 and 90.
    'xG' is the score of the expected goal at that minute, and must be a float between 0 and 1.
    'isAway' is a boolean of whether the xG belongs to the home or away team.

    Example ==========
    xG_bars([(12, 0.76, True), (42, 0.5, False), (50, 0.67, False), (77, 0.23, True)])
    """

    # draw the timeline
    for minute in range(MATCH_TIME):
        draw_xg_bar(minute=minute)

    for score in xG_scores:
        time, xG, isAway = score[0], score[1], score[2]
        assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"
        assert 0 <= time <= 90, "Minutes must be a value between 0 and 90 inclusive"
        assert isinstance(time, int), "Minutes must be an integer"
        draw_xg_bar(minute=time, xG=xG, isAway=isAway, color=get_rgb_from_xg(xG))


def load_match_data(filepath):
    """
    Assumes the file is a csv event data file from Wyscout containing only Shots events with the following columns:
        - teamId
        - xG
        - eventSec
    :return: the time in minutes (index) of each shot and its respective xG, for two teams.
    """
    match = pd.read_csv(filepath)
    team1 = match[match['teamId'] == match['teamId'].unique()[0]].copy()
    team2 = match[match['teamId'] == match['teamId'].unique()[1]].copy()

    team1['eventMin'] = team1['eventSec'].apply(lambda row: round(row / 60))
    team2['eventMin'] = team2['eventSec'].apply(lambda row: round(row / 60))

    team1_xG, team1_mins = list(team1.groupby('eventMin')['xG'].mean()), team1.groupby('eventMin')['xG'].mean().index
    team2_xG, team2_mins = list(team2.groupby('eventMin')['xG'].mean()), team2.groupby('eventMin')['xG'].mean().index

    return team1_mins, team1_xG, team2_mins, team2_xG


# scores = [(i, i/90, False) for i in range(91)]

# test on real data for England events over all the matches in Wyscout dataset.
team1_mins, team1_xG, team2_mins, team2_xG = load_match_data(r"C:\Users\anas3\Desktop\ETH\xG-data.csv")
results = [(min1, xG1, False) for min1, xG1 in zip(team1_mins, team1_xG)]
results.extend([(min2, xG2, True) for min2, xG2 in zip(team2_mins, team2_xG)])
xG_bars(results)

# Set the aspect ratio to equal and adjust the limits
# ax.set_xlim(0, 1)
# ax.set_ylim(0, 1)

# Show the plot
plt.show()
