import os
from matplotlib.patches import Circle, Rectangle, PathPatch
from matplotlib.path import Path
from typing import List, Tuple, Union
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from PIL import Image


class Serif(PathPatch):
    def __init__(self, xy, width, height, **kwargs):
        self._x, self._y = xy
        self._w, self._h = width, height
        self._x -= self._w / 4
        verts, codes = self._get_verts_and_codes()
        path = Path(verts, codes)
        super().__init__(path, edgecolor='none', **kwargs)

    def _get_verts_and_codes(self):
        # Generate the vertices of the Serif shape
        """

              |G\                             |E \
             |    \                         |     \
            |       \                     |         \
           |           \                |             \
          H              -  __ F __  -                 D
            \                                      /
               \                                /
                  \                           /
                     I                     C
                       \                  /
                        |                 |
                        |                 |
                        A _______________ B

        THE FIGURE IS NOT DRAWN TO SCALE
        """
        A = (self._x + self._w / 4, self._y)
        B = (self._x + self._w * 3 / 4, self._y)
        C = (self._x + self._w * 3 / 4, self._y + self._h * 2 / 5)
        D = (self._x + self._w * 9 / 10, self._y + self._h * 4 / 5)
        E = (self._x + self._w * 8 / 10, self._y + self._h * 0.9)
        F = (self._x + self._w / 2, self._y + self._h * 3 / 5)
        G = (self._x + self._w * 2 / 10, self._y + self._h * 0.9)
        H = (self._x + self._w * 1 / 10, self._y + self._h * 4 / 5)
        I = (self._x + self._w / 4, self._y + self._h * 2 / 5)
        verts = [A, B, C, D, E, F, G, H, I, A]
        codes = [Path.MOVETO,
                 Path.LINETO,
                 Path.CURVE3,
                 Path.CURVE3,
                 Path.LINETO,
                 Path.CURVE3,
                 Path.CURVE3,
                 Path.LINETO,
                 Path.CURVE3,
                 Path.CURVE3]
        return verts, codes


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

    def __init__(self,
                 home_scores: List[Union[Tuple[int, float, bool], Tuple[int, float]]] = None,
                 away_scores: List[Union[Tuple[int, float, bool], Tuple[int, float]]] = None,
                 match_time: int = 90,
                 timeline_color: tuple = (0.85, 0.85, 0.85),  # corresponds to xG = 0.11 (the average)
                 timeline_ticks_type: str = 'hole',
                 timeline_height: float = 0.25,
                 bars_width: float = 0.5,
                 bars_height: float = 2.4,
                 has_serif: bool = True,
                 dynamic_width: bool = True,
                 center_ticks: bool = False,
                 show: bool = True,
                 saveto: str = None):
        """
        :param home_scores: a list of 3D or 4D Tuples of the form (minute, xG, isGoal) of the home team. Where:
            - 'minute' is the time of when the shot was taken.
            - 'xG' is the xG score of the shot.
            - 'isGoal' (optional) whether the shot resulted in a
              goal or not, defaults to False (no goal).
        :param away_scores: same as 'home_scores' parameter except the Tuples are for the away team.
        :param match_time: the time of the match for which the xG has been recorded.
        :param timeline_color: the color of the timeline (x-axis). Set to black by default.
        :param timeline_ticks_type: the type of ticks drawn on the timeline. Can be one of following values:
        ['bar', 'hole', 'gap']. Set to 'bar' by default.
        :param timeline_height: the height of the timeline (x-axis).
        :param bars_width: the width of all xG bars. Defaults to 0.2
        :param bars_height: the height of the xG bars. Defaults to 1.0
        :param has_serif: if True, the white outlines around each goal circle will have a serif from the bar.
        :param dynamic_width: if True, the width of each bar will increase by xG/2.
        :param show: if True (default), the figure will be displayed in a pop-up window.
        :param saveto: the path where the figure will be saved. Defaults to 'None' (do not save the figure). Save as
        .png if you want the background to be transparent.
        Example of a valid file path: `C:/Users/xx/Desktop/myFig.png` or `./myFig.jpg`.
        If file name and extension are not provided, the default UID of the figure will be used as the name with .png extension.
        """
        # Create a figure and axes
        MIN_POINT = (0.5 - bars_height - 0.05) - (bars_width + bars_height / 10)
        MAX_POINT = (0.5 + bars_height + 0.05) + (bars_width + bars_height / 10)
        FIG_HEIGHT = MAX_POINT - MIN_POINT
        FIG_WIDTH = (match_time / 10) * (bars_width / 0.1)
        timeline_length = FIG_WIDTH
        self._fig = plt.figure(figsize=(FIG_WIDTH * 0.9, FIG_HEIGHT))
        self._ax = plt.axes([0, 0, 1, 1], frameon=False)
        self._fig.patch.set_alpha(0)
        self._ax.grid(False)
        self._ax.get_xaxis().set_visible(False)
        self._ax.get_yaxis().set_visible(False)
        self._ax.set_aspect("equal")
        self._ax.autoscale(tight=True)

        # Global xGBars configurations
        self.bars_width = bars_width
        self.match_time = match_time
        self.timeline_height = timeline_height
        self.center_ticks = center_ticks
        self.timeline_color = timeline_color
        self.timeline_ticks_type = timeline_ticks_type
        self.has_serifs = has_serif

        # check the input is correct and valid
        self._validate_parameters(bars_height, bars_width, saveto)

        # store the shots tuples as Shot object for processing. If tuple is 2D assume the 3rd value 'isGoal' is False.
        home_scores = [] if home_scores is None else home_scores
        home_shots = [Shot(ho[0], ho[1], False, (ho[2] if len(ho) == 3 else False)) for ho in home_scores]

        away_scores = [] if away_scores is None else away_scores
        away_shots = [Shot(aw[0], aw[1], True, (aw[2] if len(aw) == 3 else False)) for aw in away_scores]

        all_shots = home_shots + away_shots

        self._create_xGBars(shots_list=all_shots,
                            timeline_color=timeline_color,
                            timeline_ticks_type=timeline_ticks_type,
                            timeline_length=timeline_length,
                            bars_height=bars_height,
                            dynamic_width=dynamic_width
                            )

        # save the figure and/or display it on screen.
        if saveto is not None:
            self._save_figure(saveto)

        if show:
            plt.show()
        else:
            plt.close()

    def _draw_xg_bar(self, width: float,
                     minute: int,
                     color: tuple,
                     height: float,
                     isAway: bool,
                     isGoal: bool):
        """
        Draw a single xG bar along the timeline axis. If the xG results in a goal, a circle will also be drawn on the
        bar to indicate a goal. Away team is plotted under the timeline while the home team is plotted over it.
        :param width: the width of the bar.
        :param color: the color of the bar.
        :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
        :param isAway: whether the xG belongs to the away team or the home team.
        :param height: the height of the bar.
        :param isGoal: whether the shot resulted in a goal or not. Set to False by default.
        """
        minute = (minute / 10) * (self.bars_width / 0.1)
        BAR_X_POSITION = (minute - width / 2) if self.center_ticks else minute
        CIRCLE_X_POSITION = minute if self.center_ticks else (minute + width / 2)
        CIRCLE_RADIUS = self.bars_width * 1.5

        if isAway:  # below the timeline axis
            BAR_Y_POSITION = 0.5 - self.timeline_height / 2
            # CIRCLE_Y_POSITION = -height + BAR_Y_POSITION - 0.5  # goal circles center align with top of bars
            # CIRCLE_Y_POSITION = -height + BAR_Y_POSITION - 0.5 + CIRCLE_RADIUS  # goal circles top align with bars top
            CIRCLE_Y_POSITION = -height + BAR_Y_POSITION - CIRCLE_RADIUS*1.5  # third alignment
            UNDERLINE_HEIGHT = self.timeline_height
            height = (-1 * height)
        else:  # above the timeline axis
            BAR_Y_POSITION = 0.5 + self.timeline_height / 2
            # CIRCLE_Y_POSITION = height + BAR_Y_POSITION + 0.5  # goal circles center align with top of bars
            # CIRCLE_Y_POSITION = height + BAR_Y_POSITION - CIRCLE_RADIUS + 0.5  # goal circles top align with bars top
            CIRCLE_Y_POSITION = height + BAR_Y_POSITION + CIRCLE_RADIUS*1.5  # third alignment

            UNDERLINE_HEIGHT = -self.timeline_height

        # Draw a line underneath each bar
        bar_underline = Rectangle(xy=(BAR_X_POSITION, BAR_Y_POSITION), width=width, height=UNDERLINE_HEIGHT,
                                  fc=color)  # fc = self.timeline_color
        self._ax.add_patch(bar_underline)

        if isGoal:
            # Draw serifs on the bar's edges
            # GOAL_BAR_HEIGHT = height + 1.9 if isAway else height - 1.9  # goal circles top align with bars top
            # GOAL_BAR_HEIGHT = height + 1.25 if isAway else height - 1.25  # goal circles center align with top of bars
            GOAL_BAR_HEIGHT = height + 0.5 if isAway else height - 0.5  # third alignment

            if self.has_serifs:
                SERIF_Y_POSITION = BAR_Y_POSITION + GOAL_BAR_HEIGHT
                SERIF_Y_POSITION = SERIF_Y_POSITION + 0.01 if isAway else SERIF_Y_POSITION - 0.01  # removes sep. line
                SERIF_HEIGHT = -0.75 if isAway else 0.75
                SERIF_WIDTH = width * 2
                serif = Serif(xy=(BAR_X_POSITION, SERIF_Y_POSITION), width=SERIF_WIDTH, height=SERIF_HEIGHT, fc=color)
                self._ax.add_patch(serif)

            # Draw a shorter bar
            bar = Rectangle(xy=(BAR_X_POSITION, BAR_Y_POSITION), width=width, height=GOAL_BAR_HEIGHT, fc=color)
            self._ax.add_patch(bar)

            # Draw the circle above the bar
            goal = Circle(xy=(CIRCLE_X_POSITION, CIRCLE_Y_POSITION), radius=CIRCLE_RADIUS, fc='black')
            self._ax.add_patch(goal)
        else:
            # Draw the bar only
            height = height - 0.5 if isAway else height + 0.5
            bar = Rectangle(xy=(BAR_X_POSITION, BAR_Y_POSITION), width=width, height=height, fc=color)
            self._ax.add_patch(bar)

    def _draw_timeline(self, length: float, axis_color: Tuple[float, float, float]):

        # draw the timeline (x-axis) line
        timeline_y_position = 0.5 - self.timeline_height / 2
        timeline = Rectangle(xy=(0, timeline_y_position), width=length, height=self.timeline_height, fc=axis_color)
        self._ax.add_patch(timeline)

    def _draw_timeline_ticks(self, color, type):
        for minute in range(self.match_time + 2):
            tick_x_position = (minute / 10) * (self.bars_width / 0.1)

            # draw tick for every 15 minute. And a bigger tick for minute 45 (half-time).
            if type == "bar":
                if minute % 15 == 0:
                    if minute % 45 == 0:
                        tick_height = self.timeline_height + 1
                        tick_width = (self.bars_width / 5.0) * 2
                        tick_y_position = (0.5 - self.timeline_height / 2) - (
                                    (tick_height - self.timeline_height) / 2.0)
                        mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                              width=tick_width, height=tick_height, fc=color)
                    else:
                        tick_height = self.timeline_height + 0.5
                        tick_width = self.bars_width / 5.0
                        tick_y_position = (0.5 - self.timeline_height / 2) - (
                                    (tick_height - self.timeline_height) / 2.0)
                        mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                              width=tick_width, height=tick_height, fc=color)
                    self._ax.add_patch(mins_tick)

            elif type == "hole":
                if minute % 15 == 0 and minute != 0 and minute != self.match_time:
                    tick_radius = self.timeline_height
                    tick_y_position = 0.5
                    mins_tick = Circle(xy=(tick_x_position, tick_y_position), radius=tick_radius, fc='white')
                    self._ax.add_patch(mins_tick)

            else:  # ticks_type = 'gap'
                if minute % 15 == 0 and minute != 0 and minute != self.match_time:
                    tick_width = self.bars_width if minute % 45 == 0 else self.bars_width / 3.0
                    tick_height = self.timeline_height
                    tick_y_position = (0.5 - self.timeline_height / 2.0) - ((tick_height - self.timeline_height) / 2.0)
                    mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                          width=tick_width, height=tick_height, fc='white')
                    self._ax.add_patch(mins_tick)

    def _create_xGBars(self, shots_list: List[Shot],
                       timeline_color: Tuple[float, float, float],
                       timeline_length: float,
                       bars_height: float,
                       timeline_ticks_type: str,
                       dynamic_width: bool):
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

        self._draw_timeline(length=timeline_length, axis_color=timeline_color)

        # draw the xG bars for the home team shots
        goals = []  # keep shots with goals aside and draw them at the end.
        for shot in shots_list:
            time, xG, isAway, isGoal = shot.minute, shot.xG, shot.isAway, shot.isGoal
            self._validate_score(time, xG, isAway, isGoal)

            if isGoal:
                goals.append(Shot(time, xG, isAway, isGoal))
            else:
                bar_width = (self.bars_width + xG) if dynamic_width else self.bars_width
                if time == 88:
                    bar_width = min(bar_width, 1)
                elif time == 89:
                    bar_width = min(bar_width, self.bars_width)

                bar_color = self.get_rgb_from_xg(xG)
                self._draw_xg_bar(width=bar_width,
                                  minute=time,
                                  color=bar_color,
                                  isAway=isAway,
                                  isGoal=isGoal,
                                  height=bars_height)

        # draw the xG bars with goals at the end to be displayed on front
        for goal in goals:
            bar_width = (self.bars_width + goal.xG) if dynamic_width else self.bars_width
            if goal.minute == 88:
                bar_width = min(bar_width, 1)
            elif goal.minute == 89:
                bar_width = min(bar_width, self.bars_width)

            bar_color = self.get_rgb_from_xg(goal.xG)
            self._draw_xg_bar(minute=goal.minute,
                              width=bar_width,
                              color=bar_color,
                              isAway=goal.isAway,
                              isGoal=goal.isGoal,
                              height=bars_height)

        self._draw_timeline_ticks(color=timeline_color, type=timeline_ticks_type)

    def _validate_parameters(self, bars_height, bars_width, saveto):
        assert self.match_time > 0, "Match time cannot be 0 or a negative number"
        assert self.timeline_height > 0, "The timeline cannot have a height of 0 or negative number"
        assert bars_height > 0, "The xG bars' heights cannot be a 0 or negative number"
        assert bars_width > 0, "The xG bars' width cannot be a 0 or negative number"
        assert self.timeline_ticks_type in ['bar', 'hole', 'gap'], \
            "Invalid 'timeline_ticks_type' parameter, must be one of those values: ['bar', 'hole', 'gap']"
        if saveto is not None:
            assert os.path.isdir(os.path.dirname(saveto)), f"The provided file path {saveto} doesn't exist"

    def _validate_score(self, time, xG, isAway, isGoal):
        assert 0 <= xG <= 1, "xG score must be a value between 0 and 1 inclusive"
        assert 0 <= time <= self.match_time, "Minutes must be a value between 0 and the match time inclusive"
        assert isinstance(time, int), "Minutes must be an integer"
        assert isinstance(xG, float) or isinstance(xG, int), "xG score must be an integer or a float"
        assert isinstance(isAway, bool), "isAway must be a boolean"
        assert isinstance(isGoal, bool), "isGoal must be a boolean"

    def _save_figure(self, saveto):
        # NOTE: saving the figure as .png with `timeline_tick_type` set to any value other than 'bar' is slow
        # in processing, since the image is reloaded and saved twice for background removal.
        directory, file_name = os.path.split(saveto)
        filename, extension = os.path.splitext(file_name)

        # if the provided path doesn't contain the filename and extension, save file as png with current time name
        if filename == '' or extension == '':
            new_file_path = os.path.join(f"{saveto}", f"{id(self._fig)}.png")
            print(f"The figure is saved as `{new_file_path}`,"
                  f"since the provided path `{saveto}` doesn't contain the file name and its extension")
            saveto = new_file_path
            extension = '.png'

        # if the file is saveed as a png and contains white elements,
        # the white background and elements
        should_remove_background = (extension.lower() == '.png') and (self.timeline_ticks_type != 'bar')
        if should_remove_background:
            plt.savefig(saveto, transparent=True)
            self.remove_white_from_image(saveto, saveto)
        else:
            plt.savefig(saveto)
        print(f"File `{saveto}` has been saved sucessfully")

    @staticmethod
    def get_rgb_from_xg(xG):
        """
        Given an xG score, return a color that correponds to it. The higher the xG the darker the color. By default the
        color uses linear interpolation, where xG = 1 is black and xG = 0 is white.
        :param xG: the expected goal score between [0, 1].
        :return: 3D Tuple represnting the RGB colors.
        """
        # the colors will be scaled from 0 to 1 according to a a linearly interpolated cumulitive distribution function
        # based on the StatsBomb open-data dataset of xG scores.
        # Calculate interpolated color values
        cdf = interp1d(x=[0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04,
                          0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08, 0.085,
                          0.09, 0.095, 0.1, 0.105, 0.11, 0.115, 0.12, 0.125, 0.13,
                          0.135, 0.14, 0.145, 0.15, 0.155, 0.16, 0.165, 0.17, 0.175,
                          0.18, 0.185, 0.19, 0.195, 0.2, 0.205, 0.21, 0.215, 0.22,
                          0.225, 0.23, 0.235, 0.24, 0.245, 0.25, 0.255, 0.26, 0.265,
                          0.27, 0.275, 0.28, 0.285, 0.29, 0.295, 0.3, 0.305, 0.31,
                          0.315, 0.32, 0.325, 0.33, 0.335, 0.34, 0.345, 0.35, 0.355,
                          0.36, 0.365, 0.37, 0.375, 0.38, 0.385, 0.39, 0.395, 0.4,
                          0.405, 0.41, 0.415, 0.42, 0.425, 0.43, 0.435, 0.44, 0.445,
                          0.45, 0.455, 0.46, 0.465, 0.47, 0.475, 0.48, 0.485, 0.49,
                          0.495, 0.5, 0.505, 0.51, 0.515, 0.52, 0.525, 0.53, 0.535,
                          0.54, 0.545, 0.55, 0.555, 0.56, 0.565, 0.57, 0.575, 0.58,
                          0.585, 0.59, 0.595, 0.6, 0.605, 0.61, 0.615, 0.62, 0.625,
                          0.63, 0.635, 0.64, 0.645, 0.65, 0.655, 0.66, 0.665, 0.67,
                          0.675, 0.68, 0.685, 0.69, 0.695, 0.7, 0.705, 0.71, 0.715,
                          0.72, 0.725, 0.73, 0.735, 0.74, 0.745, 0.75, 0.755, 0.76,
                          0.765, 0.77, 0.775, 0.78, 0.785, 0.79, 0.795, 0.8, 0.805,
                          0.81, 0.815, 0.82, 0.825, 0.83, 0.835, 0.84, 0.845, 0.85,
                          0.855, 0.86, 0.865, 0.87, 0.875, 0.88, 0.885, 0.89, 0.895,
                          0.9, 0.905, 0.91, 0.915, 0.92, 0.925, 0.93, 0.935, 0.94,
                          0.945, 0.95, 0.955, 0.96, 0.965, 0.97, 0.975, 0.98, 0.985,
                          0.99, 0.995, 1.0],
                       y=[0.0, 0.00358416, 0.06358493, 0.10126705, 0.14377325,
                          0.20354154, 0.26360043, 0.31499923, 0.36145769, 0.40644374,
                          0.44550139, 0.48314476, 0.51906386, 0.55300682, 0.58270691,
                          0.60899721, 0.63377635, 0.65582378, 0.67562384, 0.69397086,
                          0.71018676, 0.7254146, 0.73856944, 0.75042622, 0.76141119,
                          0.77195056, 0.78113376, 0.78971637, 0.79769839, 0.80548667,
                          0.8125, 0.81926147, 0.82584857, 0.83113763, 0.83611671,
                          0.84115391, 0.84578425, 0.85056959, 0.85446373, 0.85857099,
                          0.86322071, 0.86692111, 0.87017591, 0.8741088, 0.87761547,
                          0.88054092, 0.88375697, 0.88668242, 0.8895885, 0.89264957,
                          0.89530378, 0.89727991, 0.89975976, 0.90225899, 0.90423512,
                          0.90659873, 0.9086911, 0.91060911, 0.91264337, 0.91483261,
                          0.91644064, 0.91851364, 0.92029603, 0.92213655, 0.92384144,
                          0.92521699, 0.92684439, 0.9283943, 0.92996358, 0.93145536,
                          0.93310214, 0.93422582, 0.93571761, 0.93709315, 0.93810059,
                          0.93937926, 0.94025108, 0.94174287, 0.94307967, 0.9441646,
                          0.9454239, 0.94650883, 0.94771001, 0.94877557, 0.94997675,
                          0.95108106, 0.95193351, 0.95274721, 0.95369653, 0.95480084,
                          0.95588577, 0.95673822, 0.95751317, 0.95815251, 0.95884997,
                          0.95968304, 0.96051612, 0.96123295, 0.96204665, 0.96287973,
                          0.96353844, 0.96410028, 0.96512709, 0.96570831, 0.9662314,
                          0.96673512, 0.96731634, 0.96776193, 0.96826565, 0.96861438,
                          0.96913748, 0.96969932, 0.97002867, 0.9704549, 0.97091987,
                          0.9712686, 0.97173357, 0.97206293, 0.97241166, 0.97264414,
                          0.97287663, 0.97320598, 0.97351596, 0.97382595, 0.97407781,
                          0.97431029, 0.97469777, 0.97500775, 0.97527898, 0.97556959,
                          0.97564709, 0.97589895, 0.97617018, 0.97646079, 0.97665453,
                          0.97686764, 0.97698388, 0.97717762, 0.97742948, 0.97766197,
                          0.9778557, 0.97801069, 0.97818506, 0.97843692, 0.97857254,
                          0.97865003, 0.97884377, 0.97894064, 0.97905688, 0.9791925,
                          0.97928937, 0.97934749, 0.97959935, 0.97983184, 0.97994808,
                          0.98004495, 0.98031618, 0.99482719, 0.99492405, 0.99517591,
                          0.99533091, 0.99542777, 0.99556339, 0.99569901, 0.99581525,
                          0.99598962, 0.99612523, 0.99626085, 0.99647396, 0.9965902,
                          0.99672582, 0.99680332, 0.99693893, 0.99705518, 0.99722954,
                          0.99732641, 0.99740391, 0.99757827, 0.99775263, 0.99800449,
                          0.99819823, 0.9982951, 0.99845009, 0.99854696, 0.99876007,
                          0.99887632, 0.99903131, 0.99912818, 0.99922505, 0.99939941,
                          0.99949628, 0.99959315, 0.99967064, 0.99974814, 0.99974814,
                          0.99982564, 0.99986438, 0.9999225, 0.99994188, 0.99998063, 1.0],
                       kind='linear')
        red = 1 - float(cdf(xG))
        green = 1 - float(cdf(xG))
        blue = 1 - float(cdf(xG))
        return red, green, blue

    @staticmethod
    def remove_white_from_image(image_path, saveto):
        # Open the image
        image = Image.open(image_path)

        # Convert the image to RGBA mode
        image = image.convert("RGBA")

        # Get the image size
        width, height = image.size

        # Create a new image with transparent background
        result_image = Image.new("RGBA", (width, height), (255, 255, 255, 0))

        # Iterate over each pixel
        for x in range(width):
            for y in range(height):
                # Get the pixel color at (x, y)
                r, g, b, a = image.getpixel((x, y))

                # Check if the pixel is white or close to white
                if r >= 255 and g >= 255 and b >= 255:
                    # Set the alpha channel of white pixels to 0 (transparent)
                    result_image.putpixel((x, y), (255, 255, 255, 0))
                else:
                    # Copy the pixel from the original image
                    result_image.putpixel((x, y), (r, g, b, a))

        # Save the modified image
        result_image.save(saveto)


if __name__ == '__main__':
    myXGBars = XGBars(
        home_scores=[
            (10, 0.15604286),
            (15, 0.030795082),
            (38, 0.016441727, True),
            (45, 0.06867906),
            (50, 0.33817625, True),
            (68, 0.20962389),
            (76, 0.1623059),
            (87, 0.50960237)
        ],
        away_scores=[
            (4, 0.03983593),
            (20, 0.03294254, True),
            (23, 0.12390236),
            (35, 0.20781437),
            (47, 0.083558895),
            (62, 0.047673356),
            (69, 0.09395622, True),
            (78, 0.04492707)
        ],
        saveto=r"C:\Users\anas3\Desktop\01.png",
    )
