import os
from matplotlib.patches import Circle, Rectangle, PathPatch
from matplotlib.path import Path
from typing import List, Tuple, Union
import matplotlib.pyplot as plt
import math
from datetime import datetime
from PIL import Image
import numpy as np


# TODO:
#   - option to display the xG above
#   - package up the code as a PyPi package
#   - Add different color spectrums option


class Serif(PathPatch):
    def __init__(self, xy, width, height, inverted=False,  **kwargs):
        codes = self._get_codes()
        self._x, self._y = xy
        self._w, self._h = width, height
        self._x -= self._w/4
        if inverted:
            verts = self._get_inverted_verts()
            path = Path(verts, codes)
        else:
            verts = self._get_verts()
            path = Path(verts, codes)
        super().__init__(path, edgecolor='none', **kwargs)

    def _get_verts(self):
        # Generate the vertices of the Serif shape
        verts = [
            (self._x + self._w/4, self._y),
            (self._x + self._w*3/4, self._y),
            (self._x + self._w*3/4, self._y + self._h*3/5),
            (self._x + self._w, self._y + self._h*4/5),
            (self._x + self._w*9/10, self._y + self._h),
            (self._x + self._w/2, self._y + self._h*3/5),
            (self._x + self._w/10, self._y + self._h),
            (self._x, self._y + self._h*4/5),
            (self._x + self._w*1/4, self._y + self._h*3/5),
            (self._x + self._w / 4, self._y)
        ]
        return verts

    @staticmethod
    def _get_codes():
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
        return codes



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
                 timeline_ticks_color: tuple = (0.0, 0.0, 0.0), timeline_ticks_type: str = 'bar',
                 timeline_height: float = 0.25, bars_width: float = 0.5, bars_height: float = 2.8,
                 coloring_mode: str = 'linear', goals_outlined: str = 'white', has_serif: bool = True,
                 dynamic_width: bool = True, show: bool = True, saveto: str = None):
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
        :param timeline_ticks_type: the type of ticks drawn on the timeline. Can be one of following values:
        ['bar', 'hole', 'gap']. Set to 'bar' by default.
        :param timeline_height: the height of the timeline (x-axis).
        :param bars_width: the width of all xG bars. Defaults to 0.2
        :param bars_height: the height of the xG bars. Defaults to 1.0
        :param coloring_mode: how the darkness of the bars increase as the xG increases. Set to 'linear' by default.
        valid values are: ['linear', 'quad', 'cubic', 'sqrt'].
        :param goals_outlined: how the goals circles will be outlined. Valid values are ['same', 'white']. Set to 'same'
        by default (outlines have the same color as the xG bar).
        :param has_serif: if True, the white outlines around each goal circle will have a serif from the bar.
        :param dynamic_width: if True, the width of each bar will increase by xG/2.
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

        # check the validity of all input data
        assert self.match_time > 0, "Match time cannot be 0 or a negative number"
        assert self.timeline_height > 0, "The timeline cannot have a height of 0 or negative number"
        assert bars_height > 0, "The xG bars' heights cannot be a 0 or negative number"
        assert coloring_mode in ["linear", "cubic", "sqrt", "quad"], \
            "coloring_mode must be one of those values: ['linear', 'cubic', 'sqrt', 'quad']"
        assert bars_width > 0, "The xG bars' width cannot be a 0 or negative number"
        assert goals_outlined in ['same', 'white'], "Invalid 'goals_outlined' parameter, must be one of those values:" \
                                                    " ['same', 'white']"
        assert timeline_ticks_type in ['bar', 'hole', 'gap'], "Invalid 'timeline_ticks_type' parameter, must be one " \
                                                              "of those values: ['bar', 'hole', 'gap']"

        timeline_length = FIG_WIDTH

        # store the shots tuples as Shot object for processing. If tuple is 2D assume the 3rd value 'isGoal' is False.
        home_shots = [Shot(ho[0], ho[1], False, (ho[2] if len(ho) == 3 else False)) for ho in home_scores]
        away_shots = [Shot(aw[0], aw[1], True, (aw[2] if len(aw) == 3 else False)) for aw in away_scores]
        all_shots = home_shots + away_shots

        self._create_xGBars(shots_list=all_shots,
                            timeline_color=timeline_color,
                            timeline_ticks_color=timeline_ticks_color,
                            timeline_ticks_type=timeline_ticks_type,
                            timeline_length=timeline_length,
                            bars_height=bars_height,
                            goals_outlined=goals_outlined,
                            has_serif=has_serif,
                            dynamic_width=dynamic_width)

        # save the figure and/or display it on screen
        if saveto is not None:
            assert os.path.isdir(os.path.dirname(saveto)), f"The provided file path {saveto} doesn't exist"
            directory, file_name = os.path.split(saveto)
            filename, extension = os.path.splitext(file_name)
            # if the provided path doesn't contain the filename and extension, save file as png with current time name
            if filename == '' or extension == '':
                new_file_path = os.path.join(f"{saveto}", f"{datetime.now().strftime('%H-%M-%S-%f')}.png")
                print(f"The figure is saved as `{new_file_path}`,"
                      f"since the provided path `{saveto}` doesn't contain the file name and its extension")
                saveto = new_file_path
            # if the file is saveed as a png, remove any white background or objects from image.
            elif extension.lower() == '.png':
                plt.savefig(saveto, transparent=True)
                self.remove_white_from_image(saveto, saveto)
            else:
                plt.savefig(saveto)
            print(f"File `{saveto}` has been saved sucessfully")
        if show:
            plt.show()
        else:
            plt.close()

    def _draw_xg_bar(self, width: float, minute: int, color: tuple, height: float, isAway: bool,
                     isGoal: bool, goals_outlined: str, has_serif: bool):
        """
        Draw a single xG bar along the timeline axis. If the xG results in a goal, a circle will also be drawn on the
        bar to indicate a goal. Away team is plotted under the timeline while the home team is plotted over it.
        :param minute: the time in minutes in which the xG is to be plotted. The time must be between 0 and 90 minutes.
        :param isAway: whether the xG belongs to the away team or the home team.
        :param isGoal: whether the shot resulted in a goal or not. Set to False by default.
        :param goals_outlined: the type of outline that will be drawn around each goal circle. Valid values:
        ['white', 'same']
        :param has_serif: if True, xG bars with goals will have serifs on their top edges.
        """
        minute /= 10
        minute *= (self.bars_width / 0.1)
        bar_x_position = minute
        bar_y_position = 0.5 - self.timeline_height / 2
        circle_x_position = minute + width / 2
        circle_radius = self.bars_width + height / 10
        circle_outline_radius = circle_radius * 1.5
        if isAway:
            circle_y_position = 0.5 - height  # below the timeline axis
            height = -1 * height
        else:
            circle_y_position = 0.5 + height  # above the timeline axis

        # draw the bar
        bar = Rectangle(xy=(bar_x_position, bar_y_position), width=width, height=height, fc=color)
        self._ax.add_patch(bar)

        # if goal, draw a black circle outlined in white or same color as the xg bar
        if isGoal:
            outline_color = color
            if goals_outlined == 'same':
                circle_radius = circle_radius / 1.5
                circle_outline_radius = circle_radius + width
            elif goals_outlined == 'white':
                outline_color = 'white'

            goal = Circle(xy=(circle_x_position, circle_y_position), radius=circle_radius, fc='black')
            goal_outline = Circle(xy=(circle_x_position, circle_y_position), radius=circle_outline_radius,
                                  fc=outline_color)
            self._ax.add_patch(goal_outline)
            self._ax.add_patch(goal)

            if has_serif and goals_outlined == 'white':  # draw serifs around the outline goal circle
                serif_width = width*2
                serif_height = -0.8 if isAway else 0.8
                serif_y_position = height + 2.2 if isAway else height - 1.2
                serif = Serif(xy=(bar_x_position, serif_y_position), width=serif_width, height=serif_height, fc=color)
                self._ax.add_patch(serif)

    def _draw_timeline(self, length: float,
                       axis_color: Tuple[float, float, float],
                       ticks_color: Tuple[float, float, float],
                       ticks_type: str):

        # draw the timeline (x-axis) line
        timeline_y_position = 0.5 - self.timeline_height / 2
        timeline = Rectangle(xy=(0, timeline_y_position), width=length,
                             height=self.timeline_height, fc=axis_color)
        self._ax.add_patch(timeline)

        for minute in range(self.match_time + 2):
            tick_x_position = (minute / 10) * (self.bars_width / 0.1)

            # draw tick for every 15 minute. And a bigger tick for minute 45 (half-time).
            if ticks_type == "bar":
                if minute % 15 == 0:
                    if minute % 45 == 0:
                        tick_height = self.timeline_height + 1
                        tick_width = (self.bars_width / 5.0) * 2
                        tick_y_position = timeline_y_position - ((tick_height - self.timeline_height) / 2.0)
                        mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                              width=tick_width, height=tick_height, fc=ticks_color)
                    else:
                        tick_height = self.timeline_height + 0.5
                        tick_width = self.bars_width / 5.0
                        tick_y_position = timeline_y_position - ((tick_height - self.timeline_height) / 2.0)
                        mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                              width=tick_width, height=tick_height, fc=ticks_color)
                    self._ax.add_patch(mins_tick)

            elif ticks_type == "hole":
                if minute % 15 == 0 and minute != 0 and minute != 90:
                    tick_radius = self.timeline_height / 2.0
                    tick_y_position = 0.5
                    mins_tick = Circle(xy=(tick_x_position, tick_y_position), radius=tick_radius, fc='white')
                    self._ax.add_patch(mins_tick)

            else:  # ticks_type = 'gap'
                if minute % 15 == 0 and minute != 0 and minute != 90:
                    tick_width = self.bars_width if minute % 45 == 0 else self.bars_width / 3.0
                    tick_height = self.timeline_height
                    tick_y_position = timeline_y_position - ((tick_height - self.timeline_height) / 2.0)
                    mins_tick = Rectangle(xy=(tick_x_position, tick_y_position),
                                          width=tick_width, height=tick_height, fc='white')
                    self._ax.add_patch(mins_tick)

    def _create_xGBars(self, shots_list: List[Shot],
                       timeline_color: Tuple[float, float, float],
                       timeline_ticks_color: Tuple[float, float, float],
                       timeline_length: float,
                       bars_height: float,
                       goals_outlined: str,
                       has_serif: bool,
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
                self._draw_xg_bar(width=(self.bars_width + xG / 2.0) if dynamic_width else self.bars_width,
                                  minute=time, color=self.get_rgb_from_xg(xG),
                                  isAway=isAway, isGoal=isGoal, height=bars_height,
                                  has_serif=has_serif, goals_outlined=goals_outlined)

        # draw goal-scoring shots at the end to be displayed on front
        for goal in goals:
            self._draw_xg_bar(minute=goal.minute,
                              width=(self.bars_width + goal.xG / 2.0) if dynamic_width else self.bars_width,
                              color=self.get_rgb_from_xg(goal.xG),
                              isAway=goal.isAway,
                              isGoal=goal.isGoal,
                              height=bars_height,
                              goals_outlined=goals_outlined,
                              has_serif=has_serif)

        self._draw_timeline(length=timeline_length,
                            axis_color=timeline_color,
                            ticks_color=timeline_ticks_color,
                            ticks_type=timeline_ticks_type)

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

    @staticmethod
    def remove_white_from_image(image_path, saveto):
        # Open the image
        image = Image.open(image_path)

        # Convert the image to RGBA mode
        image = image.convert("RGBA")

        # Convert the image to a NumPy array
        np_image = np.array(image)

        # Calculate the maximum allowed RGB value for white
        max_white = (255, 255, 255)

        # Create a mask of white pixels
        white_mask = np.all(np_image[:, :, :3] >= max_white, axis=-1)

        # Set the alpha channel of white pixels to 0 (transparent)
        np_image[white_mask] = [255, 255, 255, 0]

        # Convert the NumPy array back to an image
        result_image = Image.fromarray(np_image)

        # Save the modified image
        result_image.save(saveto)


if __name__ == '__main__':
    myXGBars = XGBars(
        home_scores=[(0, 0.4), (11, 0.23, True), (15, 0.11), (38, True, 0.4), (60, 0.8, True), (72, 0.18), (75, 0.30), (89, 0.39)],
        away_scores=[(21, 0.54, True), (56, 0.6), (49, 0.15), (87, 0.39), (80, 0.14), (67, 0.11, True)],
        saveto='./myFig.png',
    )
