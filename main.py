from matplotlib.patches import Circle, Rectangle
from typing import List, Tuple, Union
import matplotlib.pyplot as plt
import pandas as pd


# TODO:
#   - More interpolation techniques in the coloring scheme.
#   - Add bar height as a measure for xG as well.
#   - Option to encapsulate the Match tuples in an object.
#   - improve load_match_data() to accept data from different sources
#   - consider the case when the input tuples are larger than 90 for one or both of the teams.

class XGBars:

    def __init__(self, data: List[Union[Tuple[int, float, bool, bool], Tuple[int, float, bool]]] = None,
                 match_time=90, timeline_color=(0.0, 0.0, 0.0), timeline_height=0.05, xg_bar_height=0.75, show=True):
        """

        :param data: A list of 3D Tuples of the form (minute, xG, isAway, isGoal),
            - 'minute' is the time of when the xG is recorded and must be an integer between 0 and 90.
            - 'xG' is the score of the expected goal at that minute, and must be a float between 0 and 1.
            - 'isAway' is a boolean of whether the xG belongs to the home or away team.
            - 'isGoal' (optional) boolean of whether the shot resulted in a goal or not. Shots that result in a goal are
                marked with a circle at the top of the xG bar. Set to false by default.
        :param match_time: the time of the match for which the xG has been recorded.
        :param timeline_color: the color of the timeline (line that divides the xG visuals to two halves). Black by default.
        :param timeline_height: the height of the timeline.
        :param xg_bar_height: the height of the xG bars.
        """
        # Create a figure and axes
        self._fig = plt.figure(figsize=(12, 6), dpi=200)
        self._ax = plt.axes([0, 0, 1, 1], frameon=True)  # change frameon = False to remove box borders
        self._ax.grid(False)
        self._ax.get_xaxis().set_visible(False)
        self._ax.get_yaxis().set_visible(False)
        self._ax.set_aspect("equal")
        self._ax.autoscale(tight=True)

        # xGBars configurations
        self.match_time = match_time
        self._total_timeline_width = self.match_time / 10
        self._xg_bar_width = 0.1
        self.timeline_color = timeline_color
        self.timeline_height = timeline_height
        self.xg_bar_height = xg_bar_height

        assert self.match_time > 0, "Match time cannot be 0 or a negative number"
        assert self.timeline_height > 0, "The timeline cannot have a height of 0 or negative number"
        assert self.xg_bar_height > 0, "The xG bars' heights cannot be a 0 or negative number"
        assert data is not None, "No data has been provided to create the xG Bars visualization"
        self.create_xGBars(data=data)
        if show:
            plt.show()
        else:
            plt.close()

    def _draw_xg_bar(self, minute: int, xG: float = 0.0, isAway: bool = False, isGoal: bool = False):
        """
        Draw a single xG bar along the timeline axis. If the xG results in a goal, a circle will also be drawn on the
        bar to indicate a goal. Away team is plotted under the timeline while the home team is plotted over it.
        :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
        :param xG: the expected goal score during this minute of play.
        :param isAway: whether the xG belongs to the away team or the home team.
        :param isGoal: whether the shot resulted in a goal or not. Set to False by default.
        """
        minute /= 10

        if isAway:
            # create the away xG bar
            away = Rectangle(xy=(minute + self._xg_bar_width, 0.5 - self.timeline_height / 2),
                             width=self._xg_bar_width, height=-self.xg_bar_height, fc=self.get_rgb_from_xg(xG))
            if isGoal:
                goal = Circle(
                    xy=(minute + self._xg_bar_width + self._xg_bar_width / 2, 0.5 - self.xg_bar_height - 0.05),
                    radius=self._xg_bar_width + self.xg_bar_height / 10, fc=self.get_rgb_from_xg(xG))
                self._ax.add_patch(goal)
            self._ax.add_patch(away)

        else:
            # create the home xG bar
            home = Rectangle(xy=(minute + self._xg_bar_width, 0.5 + self.timeline_height / 2),
                             width=self._xg_bar_width, height=self.xg_bar_height, fc=self.get_rgb_from_xg(xG))
            if isGoal:
                goal = Circle(
                    xy=(minute + self._xg_bar_width + self._xg_bar_width / 2, 0.5 + self.xg_bar_height + 0.05),
                    radius=self._xg_bar_width + self.xg_bar_height / 10, fc=self.get_rgb_from_xg(xG))
                self._ax.add_patch(goal)
            self._ax.add_patch(home)

        timeline = Rectangle(xy=(minute + self._xg_bar_width, 0.5 - self.timeline_height / 2),
                             width=self._xg_bar_width, height=self.timeline_height, fc=self.timeline_color)
        self._ax.add_patch(timeline)

    def create_xGBars(self, data):
        """
        Draw the xG Bars and timeline for an entire list of expected goals data.
        :param data: A list of 3D Tuples of the form (minute, xG, isAway, isGoal),
            - 'minute' is the time of when the xG is recorded and must be an integer between 0 and 90.
            - 'xG' is the score of the expected goal at that minute, and must be a float between 0 and 1.
            - 'isAway' is a boolean of whether the xG belongs to the home or away team.
            - 'isGoal' (optional) boolean of whether the shot resulted in a goal or not. Shots that result in a goal are
                marked with a circle at the top of the xG bar. Set to false by default.

        Example ==================
        create_XGBars([(12, 0.76, True), (42, 0.5, False), (50, 0.67, False, True), (77, 0.23, True)])
        """

        # draw the timeline
        for minute in range(self.match_time + 1):
            self._draw_xg_bar(minute=minute)  # no xG bars drawn, just the timeline

        # draw the xG bars
        for score in data:
            time, xG, isAway = score[0], score[1], score[2]
            assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"
            assert 0 <= time <= 90, "Minutes must be a value between 0 and 90 inclusive"
            assert isinstance(time, int), "Minutes must be an integer"
            if len(score) == 4:  # 'isGoal' is provided as an input.
                isGoal = score[3]
            else:
                isGoal = False
            self._draw_xg_bar(minute=time, xG=xG, isAway=isAway, isGoal=isGoal)

    @staticmethod
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

        team1_xG, team1_mins = list(team1.groupby('eventMin')['xG'].mean()), team1.groupby('eventMin')[
            'xG'].mean().index
        team2_xG, team2_mins = list(team2.groupby('eventMin')['xG'].mean()), team2.groupby('eventMin')[
            'xG'].mean().index

        return team1_mins, team1_xG, team2_mins, team2_xG

    @staticmethod
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


# test on real data for England events over all the matches in Wyscout dataset.
team1_mins, team1_xG, team2_mins, team2_xG = XGBars.load_match_data(r"C:\Users\anas3\Desktop\ETH\xG-data.csv")
results = [(min1, xG1, False) for min1, xG1 in zip(team1_mins, team1_xG)]
results.extend([(min2, xG2, True) for min2, xG2 in zip(team2_mins, team2_xG)])

myXGBars = XGBars(results, show=False)
myXGBars2 = XGBars([
    (8, 0.66, False),
    (15, 0.43, True),
    (17, 0.12, False),
    (25, 0.8, False),
    (26, 0.75, False, True),
    (29, 0.3, False),
    (39, 0.4, True),
    (45, 0.48, False, True),
    (58, 0.33, True),
    (70, 0.19, True),
    (71, 0.43, True),
    (89, 0.12, False)
])
