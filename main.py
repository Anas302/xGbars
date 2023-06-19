from matplotlib.patches import Circle, Rectangle
from typing import List, Tuple, Union
import matplotlib.pyplot as plt
import pandas as pd
import math


# TODO:
#   - Add bar height as a measure for xG as well.
#   - improve load_match_data() to accept data from different sources
#   - consider the case when the input tuples are larger than 90 for one or both of the teams.
#   - option to display the xG above
#   - package up the code as a PyPi package


class Shot:

    def __init__(self, minute: int, xG: float, isAway: bool = False, isGoal: bool = False):
        self.minute = minute
        self.xG = xG
        self.isAway = isAway
        self.isGoal = isGoal

    def __repr__(self):
        return f"Shot(minute={self.minute}, xG={self.xG}, isAway={self.isAway}, isGoal={self.isGoal})"

    def __eq__(self, other):
        return self.minute == other.minute and \
               self.xG == other.minute and \
               self.isAway == other.isAway and \
               self.isGoal == other.isGoal

    def __add__(self, other):
        if self.minute == other.minute and self.isAway == other.isAway:
            return Shot(self.minute, self.xG + other.xG, self.isAway, self.isGoal and other.isGoal)
        else:
            raise ValueError("Cannot add two shots with different timestamps or teams")


class XGBars:

    def __init__(self, data: List[Union[Tuple[int, float, bool, bool], Tuple[int, float, bool], Shot]] = None,
                 match_time: int = 90, timeline_color: tuple = (0.0, 0.0, 0.0), timeline_height: float = 0.05,
                 bars_height: float = 0.75, coloring_mode: str = 'linear', show: bool = True):
        """

        :param data:
        Either:
        > A list of 3D or 4D Tuples of the form (minute, xG, isAway, isGoal),
            - 'minute' is the time of when the xG is recorded and must be an integer between 0 and 90.
            - 'xG' is the score of the expected goal at that minute, and must be a float between 0 and 1.
            - 'isAway' is a boolean of whether the xG belongs to the home or away team.
            - 'isGoal' (optional) boolean of whether the shot resulted in a goal or not. Shots that result in a goal are
                marked with a circle at the top of the xG bar. Defaults to False if not provided.
        Or:
        > A list of Shot objects, whose parameters correspond to 'minute', 'xG', 'isAway', and 'isGoal'.
        :param match_time: the time of the match for which the xG has been recorded.
        :param timeline_color: the color of the timeline (line that divides the xG visuals to two halves). Black by default.
        :param timeline_height: the height of the timeline.
        :param bars_height: the height of the xG bars.
        """
        # Create a figure and axes
        self._fig = plt.figure(figsize=(12, 6), dpi=200)
        self._ax = plt.axes([0, 0, 1, 1], frameon=False)  # change frameon = False to remove box borders
        self._ax.grid(False)
        self._ax.get_xaxis().set_visible(False)
        self._ax.get_yaxis().set_visible(False)
        self._ax.set_aspect("equal")
        self._ax.autoscale(tight=True)

        # xGBars configurations
        self.match_time = match_time
        self.timeline_height = timeline_height
        self._XG_BAR_WIDTH = 0.2

        assert self.match_time > 0, "Match time cannot be 0 or a negative number"
        assert self.timeline_height > 0, "The timeline cannot have a height of 0 or negative number"
        assert bars_height > 0, "The xG bars' heights cannot be a 0 or negative number"
        assert data is not None, "No data has been provided to create the xG Bars visualization"
        assert coloring_mode == "linear" or coloring_mode == "cubic" or \
               coloring_mode == "sqrt" or coloring_mode == "quad", \
               "coloring_mode must be one of those values: ['linear', 'cubic', 'sqrt', 'quad']"

        self._create_xGBars(data=data, timeline_color=timeline_color,
                            timeline_length=self.match_time/10, bars_height=bars_height)
        if show:
            plt.show()
        else:
            plt.close()

    def _draw_xg_bar(self, minute: int, color: tuple, height: float, isAway: bool = False, isGoal: bool = False):
        """
        Draw a single xG bar along the timeline axis. If the xG results in a goal, a circle will also be drawn on the
        bar to indicate a goal. Away team is plotted under the timeline while the home team is plotted over it.
        :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
        :param isAway: whether the xG belongs to the away team or the home team.
        :param isGoal: whether the shot resulted in a goal or not. Set to False by default.
        """
        minute /= 10

        if isAway:
            # create the away xG bar
            away = Rectangle(xy=(minute + self._XG_BAR_WIDTH, 0.5 - self.timeline_height / 2), width=self._XG_BAR_WIDTH,
                             height=-height, fc=color)
            if isGoal:
                goal = Circle(
                    xy=(minute + self._XG_BAR_WIDTH + self._XG_BAR_WIDTH / 2, 0.5 - height - 0.05),
                    radius=self._XG_BAR_WIDTH + height / 10, fc=color)
                self._ax.add_patch(goal)
            self._ax.add_patch(away)

        else:
            # create the home xG bar
            home = Rectangle(xy=(minute + self._XG_BAR_WIDTH, 0.5 + self.timeline_height / 2),
                             width=self._XG_BAR_WIDTH, height=height, fc=color)
            if isGoal:
                goal = Circle(
                    xy=(minute + self._XG_BAR_WIDTH + self._XG_BAR_WIDTH / 2, 0.5 + height + 0.05),
                    radius=self._XG_BAR_WIDTH + height / 10, fc=color)
                self._ax.add_patch(goal)
            self._ax.add_patch(home)

    def _draw_timeline(self, timeline_length, color):
        # time axis
        timeline = Rectangle(xy=(0, 0.5 - self.timeline_height / 2), width=timeline_length,
                             height=self.timeline_height, fc=color)
        for minute in range(self.match_time - 2):
            minute /= 10
            minute += 0.1
            # coordinates of each minute
            mins_coords = Rectangle(xy=(minute + 3 * self._XG_BAR_WIDTH / 8, 0.5 - self.timeline_height),
                                    width=self._XG_BAR_WIDTH / 5, height=self.timeline_height * 2.2,
                                    fc=color)
            self._ax.add_patch(mins_coords)
            self._ax.add_patch(timeline)

    def _create_xGBars(self, data, timeline_color, timeline_length, bars_height):
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

        # draw the xG bars
        goals = []  # keep shots with goals aside and draw them at the end.
        for score in data:
            if isinstance(score, tuple):
                time, xG, isAway, isGoal = score[0], score[1], score[2], score[3] if len(score) == 4 else False
            else:
                time, xG, isAway, isGoal = score.minute, score.xG, score.isAway, score.isGoal
            assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"
            assert 0 <= time <= 90, "Minutes must be a value between 0 and 90 inclusive"
            assert isinstance(time, int), "Minutes must be an integer"
            if isGoal:
                goals.append(Shot(time, xG, isAway, isGoal))
            else:
                self._draw_xg_bar(minute=time, color=self.get_rgb_from_xg(xG),
                                  isAway=isAway, isGoal=isGoal, height=bars_height)

        # draw goal-scoring shots at the end to be on front
        for goal in goals:
            self._draw_xg_bar(minute=goal.minute,
                              color=self.get_rgb_from_xg(goal.xG),
                              isAway=goal.isAway,
                              isGoal=goal.isGoal,
                              height=bars_height)

        self._draw_timeline(color=timeline_color, timeline_length=timeline_length)

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
    def get_rgb_from_xg(xG, mode='linear'):
        """
        Given an xG score, return a color that correponds to it. The higher the xG the darker the color. By default the
        color uses linear interpolation, where xG = 1 is black and xG = 0 is white.
        :param xG: the expected goal score between [0, 1].
        :param mode: the interpolation of any xG value between 0 and 1 to its respective RGB color. Can be one of the
        following: ['linear', 'quad', 'cubic', 'sqrt']. Defaults to 'linear'. 'quad' and 'cubic' provide more emphasis
        on high xG scores. Whereas 'sqrt' provides more emphasis on low values.
        :return: 3D Tuple represnting the RGB colors.
        """

        # Calculate interpolated color values
        if mode == 'linear':
            red = 1 - xG
            green = 1 - xG
            blue = 1 - xG
        elif mode == 'sqrt':
            red = 1 - math.sqrt(xG)
            green = 1 - math.sqrt(xG)
            blue = 1 - math.sqrt(xG)
        elif mode == 'quad':
            red = 1 - xG ** 2
            green = 1 - xG ** 2
            blue = 1 - xG ** 2
        elif mode == 'cubic':
            red = 1 - xG ** 3
            green = 1 - xG ** 3
            blue = 1 - xG ** 3
        else:
            raise ValueError("The provided mode arguement is incorrect. 'mode' should be in ['linear', 'quad', 'sqrt']")
        return red, green, blue


# test on real data for England events over all the matches in Wyscout dataset.
team1_mins, team1_xG, team2_mins, team2_xG = XGBars.load_match_data(r"C:\Users\anas3\Desktop\ETH\xG-data.csv")
results = [(min1, xG1, False) for min1, xG1 in zip(team1_mins, team1_xG)]
results.extend([(min2, xG2, True) for min2, xG2 in zip(team2_mins, team2_xG)])

shots = Shot(45, 0.8, False, False) + Shot(45, 0.4, False, False)

myXGBars = XGBars(results, match_time=90, coloring_mode='cubic', show=False)
myXGBars2 = XGBars([
    (8, 0.1, False),
    (10, 0.2, False),
    (12, 0.3, False),
    (14, 0.4, False),
    (16, 0.5, False),
    (8, 0.1, True),
    (10, 0.2, True, True),
    (12, 0.3, True),
    (14, 0.4, True),
    (16, 0.5, True),
    (22, 0.6, False),
    (24, 0.7, False, True),
    (26, 0.8, False),
    (28, 0.9, False),
    (30, 1, False),
    (22, 0.6, True),
    (24, 0.7, True),
    (26, 0.8, True),
    (28, 0.9, True),
    (30, 1, True),
], match_time=90, show=False)

myXGBars3 = XGBars([
    (11, 0.23, False),
    (15, 0.11, False),
    (21, 0.54, True, True),
    (38, 0.4, False),
    (49, 0.15, True),
    (56, 0.6, True),
    (60, 0.8, False, True),
    (72, 0.18, False),
    (75, 0.30, False),
    (80, 0.14, True),
    (87, 0.39, True),
])
