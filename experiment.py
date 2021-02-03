#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The conductor of the experiments, that makes communicating with EEG and ET

Usage:
  conductor.py <NIP> <participant_number> [--no-egi] [--no-et]
  conductor.py (-h | --help)
"""

import time
import csv

from importlib import import_module
from unittest.mock import MagicMock

import docopt

import expyriment


# Parse arguments
args = docopt.docopt(__doc__)

# Useful global variable to avoid passing handles to things in callbacks
global CSV
CSV = None

# Depending on the arguments, import the true or the fake devices, to test
egi = import_module("egi.fake" if args["--no-egi"] else "egi.simple")

tr = None
if args["--no-et"]:
    tr = MagicMock()
    tr.get_system_time_stamp = lambda: time.time()
else:
    tr = import_module("tobii_research")
eyetracker = tr.EyeTracker("tet-tcp://169.254.65.21")


# Hardcoded EGI parameters at NeuroSpin
IP = "132.166.140.251"
PORT = 55513

# Define the net station at top level
net_station = egi.Netstation()


def gaze_data_callback(gaze_data):
    """
    This is the function that's called whenever new gaze data comes in. Writing
    to disk might be a bad idea if it's too slow, but so far it's been fine.
    Here you could do more fancy stuff like plotting the location or other.
    """
    global CSV
    CSV.writerow(list(gaze_data.values()))


def calibrate_block(exp):
    """
    Calibrate the ET. In order to do this, for a bunch of points, ask the
    presentation to have participants look at these poits, then record gaze,
    then calibrate.
    """

    # Feel free to replace with whatever makes you happy. From the doc:
    # The coordinates are normalized, i.e. (0.0, 0.0) is the upper left corner
    # and (1.0, 1.0) is the lower right corner.
    points_to_calibrate = [
        {"x": 0.49, "y": 0.5},
        {"x": 0.3, "y": 0.3},
        {"x": 0.3, "y": 0.7},
        {"x": 0.7, "y": 0.3},
        {"x": 0.7, "y": 0.7},
        {"x": 0.51, "y": 0.5},
    ]

    # Loop while you think you need to calibrate again
    satisfied = False
    while not satisfied:
        calibration = tr.ScreenBasedCalibration(eyetracker)
        try:
            calibration.leave_calibration_mode()
        except:
            pass
        calibration.enter_calibration_mode()
        (sx, sy) = exp.screen.size
        for point in points_to_calibrate:
            # Present at the right location and wait for keypress
            dot = expyriment.stimuli.Circle(
                20,
                position=(
                    sx * point["x"] - (sx / 2),
                    -sy * point["y"] + (sy / 2),
                ),
                anti_aliasing=32,
            )
            dot.present()
            _, _ = exp.keyboard.wait([expyriment.misc.constants.K_RIGHT])
            exp.data.add(["calibration", point["x"], point["y"]])
            send_EGI_Event(
                {"type": "calibration", "x": point["x"], "y": point["y"]}
            )
            if (
                calibration.collect_data(point["x"], point["y"])
                != tr.CALIBRATION_STATUS_SUCCESS
            ):
                calibration.collect_data(point["x"], point["y"])

        calibration_result = calibration.compute_and_apply()

        question = "Got " + str(len(calibration_result.calibration_points))
        question += " points out of 6.\nET says that status is "
        question += str(calibration_result.status)
        question += ".\nAre you satisfied? Press UP for yes and DOWN for no."

        calibration.leave_calibration_mode()

        # Check if satisfied!
        stim = expyriment.stimuli.TextBox(question, (sx, sy / 2))
        stim.present()
        key, _ = exp.keyboard.wait(
            [expyriment.misc.constants.K_UP, expyriment.misc.constants.K_DOWN]
        )
        satisfied = key == expyriment.misc.constants.K_UP

    eyetracker.subscribe_to(
        tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True
    )


def init():
    """
    When exp starts, log timestamp and initiate NetStation.
    Note that the presentation needs to be informed about the eyetracker, so we
    don't start the block right away but instead we notify the presentation of
    whether ET is in order or not.
    """
    global CSV

    # First init the eye tracker
    t_et_origin = tr.get_system_time_stamp()
    fname = "./et_data/"
    fname += args["<NIP>"] + "_" + args["<participant_number>"] + "_"
    fname += str(t_et_origin) + ".csv"
    CSV = csv.writer(
        open(fname, "w", newline="", encoding="utf-8"),
        delimiter=";",
        quoting=csv.QUOTE_MINIMAL,
    )
    # Hardcoded information that the eye tracker sends with every callback. This
    # is just so that the resulting CSV has relevant headers.
    CSV.writerow(
        [
            "device_time_stamp",
            "system_time_stamp",
            "left_gaze_point_on_display_area",
            "left_gaze_point_in_user_coordinate_system",
            "left_gaze_point_validity",
            "left_pupil_diameter",
            "left_pupil_validity",
            "left_gaze_origin_in_user_coordinate_system",
            "left_gaze_origin_in_trackbox_coordinate_system",
            "left_gaze_origin_validity",
            "right_gaze_point_on_display_area",
            "right_gaze_point_in_user_coordinate_system",
            "right_gaze_point_validity",
            "right_pupil_diameter",
            "right_pupil_validity",
            "right_gaze_origin_in_user_coordinate_system",
            "right_gaze_origin_in_trackbox_coordinate_system",
            "right_gaze_origin_validity",
        ]
    )

    net_station.connect(IP, PORT)
    net_station.BeginSession()
    net_station.sync()
    t_egi_origin = egi.ms_localtime()
    net_station.StartRecording()

    # And finaly init expyriment
    expyriment.control.defaults.window_mode = True
    expyriment.control.defaults.fast_quit = False
    expyriment.control.defaults.opengl = 2
    expyriment.control.defaults.initialize_delay = 0
    exp = expyriment.design.Experiment(name="Test")
    expyriment.control.initialize(exp)

    return exp, t_egi_origin


def quit_devices():
    """When exp terminates, close the NetStation and the ET
    """
    # Quit the ET
    eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)

    # & EGI (some sleep is needed otherwise the egi freaks out)
    net_station.StopRecording()
    time.sleep(1)
    net_station.EndSession()
    time.sleep(1)
    net_station.disconnect()

    # And also quit expryiment
    expyriment.control.end()


def send_EGI_Event(event):
    """
    Write (enhanced) dict to a net_station
    """
    event["t_py"] = egi.ms_localtime()
    event["t_et"] = tr.get_system_time_stamp()
    net_station.send_event(
        event["type"],
        label="coordinator",
        timestamp=egi.ms_localtime(),
        table=event,
    )


def main_exp():
    return None


# Write some demo exp.

if __name__ == "__main__":

    exp, t_egi_origin = init()
    expyriment.control.start(
        skip_ready_screen=True, subject_id=int(args["<NIP>"])
    )

    # Now that everything is set up, do the ET calibration
    calibrate_block(exp)

    # Now present your experiment, and don't forget to log information for each
    # presentation BOTH to expyriment with exp.data.add and to the EGI with
    # send_EGI_Event
    main_exp()

    # Now you can terminate everything
    quit_devices()
