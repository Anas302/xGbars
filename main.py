import os
from matplotlib.patches import Circle, Rectangle
from typing import List, Tuple, Union
import matplotlib.pyplot as plt
import pandas as pd
import math
from datetime import datetime


# TODO:
#   - option to display the xG above
#   - package up the code as a PyPi package
#   - Add different color spectrums option


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

    def __init__(self, home_scores: List[Union[Tuple[int, float, bool], Tuple[int, float]]] = None,
                 away_scores: List[Union[Tuple[int, float, bool], Tuple[int, float]]] = None,
                 match_time: int = 90, timeline_color: tuple = (0.0, 0.0, 0.0),
                 timeline_ticks_color: tuple = (0.0, 0.0, 0.0), timeline_height: float = 0.08,
                 bars_width: float = 0.5, bars_height: float = 2.8, coloring_mode: str = 'linear',
                 goals_outlined: str = 'same', has_serif: bool = True, show: bool = True, saveto: str = None):
        """
        :param home_scores: a list of 3D or 4D Tuples of the form (minute, xG, isGoal) of the home team. Where:
        - 'minute' is the time of when the shot was taken.
        - 'xG' is the xG score of the shot.
        - 'isGoal' (optional) whether the shot resulted in a
          goal or not, defaults to False (no goal).
        :param away_scores: same as 'home_scores' parameter except the Tuples are for the away team.
        :param match_time: the time of the match for which the xG has been recorded.
        :param timeline_color: the color of the timeline (x-axis). Set to black by default.
        :param timeline_ticks_color: the color of the timeline ticks. Set to black by default.
        :param timeline_height: the height of the timeline (x-axis).
        :param bars_width: the width of all xG bars. Defaults to 0.2
        :param bars_height: the height of the xG bars. Defaults to 1.0
        :param coloring_mode: how the darkness of the bars increase as the xG increases. Set to 'linear' by default.
        valid values are: ['linear', 'quad', 'cubic', 'sqrt'].
        :param goals_outlined: how the goals circles will be outlined. Valid values are ['same', 'white']. Set to 'same'
        by default (outlines have the same color as the xG bar).
        :param has_serif: if True, the white outlines around each goal circle will have a serif from the bar.
        :param show: if True (default), the figure will be displayed in a pop-up window.
        :param saveto: the path where the figure will be saved. Defaults to 'None' (do not save the figure). Save as
        .PNG if you want the background to be transparent.
        Example of a valid file path: `C:/Users/xx/Desktop/myFig.png` or `./myFig.jpg`.
        If the file name and extension are not provided, the current time will be used as the name with .png extension.
        """
        # Create a figure and axes
        MIN_POINT = (0.5 - bars_height - 0.05) - (bars_width + bars_height / 10)
        MAX_POINT = (0.5 + bars_height + 0.05) + (bars_width + bars_height / 10)
        FIG_HEIGHT = MAX_POINT - MIN_POINT
        FIG_WIDTH = (match_time / 10) * (bars_width / 0.1)
        self._fig = plt.figure(figsize=(FIG_WIDTH * 0.9, FIG_HEIGHT))
        self._ax = plt.axes([0, 0, 1, 1], frameon=False)  # change frameon = False to remove box borders
        self._fig.patch.set_alpha(0)
        self._ax.grid(False)
        self._ax.get_xaxis().set_visible(False)
        self._ax.get_yaxis().set_visible(False)
        self._ax.set_aspect("equal")
        self._ax.autoscale(tight=True)

        # xGBars configurations
        self.bars_width = bars_width
        self.match_time = match_time
        self.timeline_height = timeline_height

        assert self.match_time > 0, "Match time cannot be 0 or a negative number"
        assert self.timeline_height > 0, "The timeline cannot have a height of 0 or negative number"
        assert bars_height > 0, "The xG bars' heights cannot be a 0 or negative number"
        assert coloring_mode == "linear" or coloring_mode == "cubic" or \
               coloring_mode == "sqrt" or coloring_mode == "quad", \
               "coloring_mode must be one of those values: ['linear', 'cubic', 'sqrt', 'quad']"
        assert bars_width > 0, "The xG bars' width cannot be a 0 or negative number"
        assert goals_outlined in ['same', 'white'], "Invalid 'goals_outlined' parameter, must be one of those values:" \
                                                    " ['same', 'white']"

        timeline_length = FIG_WIDTH
        # store the shots tuples as Shot object for processing. If tuple is 2D assume the 3rd value 'isGoal' is False.
        home_shots = [Shot(ho[0], ho[1], False, (ho[2] if len(ho) == 3 else False)) for ho in home_scores]
        away_shots = [Shot(aw[0], aw[1], True, (aw[2] if len(aw) == 3 else False)) for aw in away_scores]
        all_shots = home_shots + away_shots

        self._create_xGBars(shots_list=all_shots,
                            timeline_color=timeline_color,
                            timeline_ticks_color=timeline_ticks_color,
                            timeline_length=timeline_length,
                            bars_height=bars_height,
                            goals_outlined=goals_outlined,
                            has_serif=has_serif)

        if saveto is not None:
            assert os.path.isdir(os.path.dirname(saveto)), f"The provided file path {saveto} doesn't exist"
            directory, file_name = os.path.split(saveto)
            filename, extension = os.path.splitext(file_name)
            if filename == '' or extension == '':
                new_file_path = os.path.join(f"{saveto}", f"{datetime.now().strftime('%H-%M-%S-%f')}.png")
                print(f"The figure is saved as `{new_file_path}`,"
                      f"since the provided path `{saveto}` doesn't contain the file name and its extension")
                saveto = new_file_path
            plt.savefig(saveto, transparent=True)
            print(f"File `{saveto}` has been saved sucessfully")
        if show:
            plt.show()
        else:
            plt.close()

    def _draw_xg_bar(self, minute: int, color: tuple, height: float, isAway: bool, isGoal: bool,
                     goals_outlined: str, has_serif: bool):
        """
        Draw a single xG bar along the timeline axis. If the xG results in a goal, a circle will also be drawn on the
        bar to indicate a goal. Away team is plotted under the timeline while the home team is plotted over it.
        :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
        :param isAway: whether the xG belongs to the away team or the home team.
        :param isGoal: whether the shot resulted in a goal or not. Set to False by default.
        """
        minute /= 10
        minute *= (self.bars_width / 0.1)
        bar_x_position = minute
        bar_y_position = 0.5 - self.timeline_height / 2
        circle_x_position = minute + self.bars_width / 2
        circle_radius = self.bars_width + height / 10
        circle_outline_radius = circle_radius * 1.5

        if isAway:
            circle_y_position = 0.5 - height  # below the timeline axis
            height = -1 * height
        else:
            circle_y_position = 0.5 + height  # above the timeline axis

        # draw the bar
        bar = Rectangle(xy=(bar_x_position, bar_y_position), width=self.bars_width, height=height, fc=color)
        self._ax.add_patch(bar)

        # if goal, draw a black circle outlined in white or same color as the xg bar
        if isGoal:
            outline_color = color
            if goals_outlined == 'same':
                circle_radius = circle_radius / 1.5
                circle_outline_radius = circle_radius + self.bars_width
            elif goals_outlined == 'white':
                outline_color = 'white'

            if has_serif and goals_outlined == 'white':  # draw serifs around the outline goal circle
                serif_radius = circle_outline_radius / 2
                serif_y_position = height + 1.25 if isAway else height - 0.25
                serif = Circle(xy=(circle_x_position, serif_y_position), radius=serif_radius, fc=color)
                self._ax.add_patch(serif)

            goal = Circle(xy=(circle_x_position, circle_y_position), radius=circle_radius, fc='black')
            goal_outline = Circle(xy=(circle_x_position, circle_y_position), radius=circle_outline_radius, fc=outline_color)
            self._ax.add_patch(goal_outline)
            self._ax.add_patch(goal)

    def _draw_timeline(self, timeline_length: float,
                       axis_color: Tuple[float, float, float],
                       ticks_color: Tuple[float, float, float]):

        timeline_y_position = 0.5 - self.timeline_height / 2
        for minute in range(self.match_time + 2):
            tick_x_position = (minute / 10) * (self.bars_width / 0.1)

            # draw tick for every 15 minute. And a bigger tick for minute 45
            if minute % 45 == 0:
                tick_height = self.timeline_height * 12
                tick_width = (self.bars_width / 5.0) * 2
                tick_y_position = timeline_y_position - ((tick_height - self.timeline_height) / 2.0)
                mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                      width=tick_width, height=tick_height, fc=ticks_color)
                self._ax.add_patch(mins_tick)

            elif minute % 15 == 0:
                tick_height = self.timeline_height * 8.0
                tick_width = self.bars_width / 5.0
                tick_y_position = timeline_y_position - ((tick_height - self.timeline_height) / 2.0)
                mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                      width=tick_width, height=tick_height,
                                      fc=ticks_color)
                self._ax.add_patch(mins_tick)
            # else:
            #     mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
            #                           width=tick_width, height=tick_height,
            #                           fc=ticks_color)

        # time axis
        timeline = Rectangle(xy=(0, timeline_y_position), width=timeline_length,
                             height=self.timeline_height, fc=axis_color)
        self._ax.add_patch(timeline)

    def _create_xGBars(self, shots_list: List[Shot],
                       timeline_color: Tuple[float, float, float],
                       timeline_ticks_color: Tuple[float, float, float],
                       timeline_length: float,
                       bars_height: float,
                       goals_outlined: str,
                       has_serif: bool):
        """
        Draw the xG Bars and timeline for an entire list of expected goals data.
        :param shots_list: A list of 'Shot' objects in which the attributes:
            - 'minute' is the time of when the xG is recorded and must be an integer between 0 and 90.
            - 'xG' is the score of the expected goal at that minute, and must be a float between 0 and 1.
            - 'isAway' is a boolean of whether the xG belongs to the home or away team.
            - 'isGoal' (optional) boolean of whether the shot resulted in a goal or not. Shots that result in a goal are
                marked with a circle at the top of the xG bar. Set to false by default.

        Example ==================
        create_XGBars([Shot(12, 0.76, True), Shot(42, 0.5, False), Shot(50, 0.67, False, True), Shot(77, 0.23, True)])
        """

        # draw the xG bars for the home team shots
        goals = []  # keep shots with goals aside and draw them at the end.
        for shot in shots_list:
            time, xG, isAway, isGoal = shot.minute, shot.xG, shot.isAway, shot.isGoal
            assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"
            assert 0 <= time <= self.match_time, "Minutes must be a value between 0 and the match time inclusive"
            assert isinstance(time, int), "Minutes must be an integer"
            if isGoal:
                goals.append(Shot(time, xG, isAway, isGoal))
            else:
                self._draw_xg_bar(minute=time, color=self.get_rgb_from_xg(xG),
                                  isAway=isAway, isGoal=isGoal, height=bars_height,
                                  has_serif=has_serif, goals_outlined=goals_outlined)

        # draw goal-scoring shots at the end to be displayed on front
        for goal in goals:
            self._draw_xg_bar(minute=goal.minute,
                              color=self.get_rgb_from_xg(goal.xG),
                              isAway=goal.isAway,
                              isGoal=goal.isGoal,
                              height=bars_height,
                              goals_outlined=goals_outlined,
                              has_serif=has_serif)

        self._draw_timeline(timeline_length=timeline_length,
                            axis_color=timeline_color,
                            ticks_color=timeline_ticks_color)



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


if __name__ == '__main__':
    # test on real data for England events over all the matches in Wyscout dataset.
    team1_mins, team1_xG, team2_mins, team2_xG = XGBars.load_match_data(r"C:\Users\anas3\Desktop\ETH\xG-data.csv")
    results = [(min1, xG1, False) for min1, xG1 in zip(team1_mins, team1_xG)]
    results.extend([(min2, xG2, True) for min2, xG2 in zip(team2_mins, team2_xG)])

    myXGBars3 = XGBars(
        home_scores=[(0, 0.4), (11, 0.23), (15, 0.11), (38, 0.4), (60, 0.8, True), (72, 0.18), (75, 0.30), (89, 0.39)],
        away_scores=[(21, 0.54, True), (56, 0.6), (49, 0.15), (87, 0.39), (80, 0.14), (67, 0.11, True)],
        goals_outlined='white',
        saveto='./myFig.png'
    )
