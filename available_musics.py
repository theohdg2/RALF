from wumons import Music

"""
    :class AvailableMusics: This class contains predefined music sequences that can be played using the wukong Music Player. Each music sequence is represented as a list of notes and their durations.
"""


class AvailableMusics(Music):
    LASER_BEAM = [
        "c6:1", "b5:1", "a5:1", "g5:1", "f5:1", "e5:1", "d5:1", "c5:2",
        "c6:1", "b5:1", "a5:1", "g5:1", "f5:1", "e5:1", "d5:1", "c5:4"
    ]

    NOKIA_TUNE = [
        "e5:1", "d5:1", "f#4:2", "g#4:2",
        "c#5:1", "b4:1", "d4:2", "e4:2",
        "b4:1", "a4:1", "c#4:2", "e4:2", "a4:4"
    ]
    BT_CONNECTED = ["e5:1", "g#5:3"]
    BOOTLOADER_ACTIVE = ["c#5:1", "e5:1", "g#5:1", "c#6:1"]
    BT_DISCONNECTED = ["g#5:1", "e5:2", "b4:3"]

    SUCCESS_START = ["f#5:1", "b5:1", "c#6:1", "d#6:2"]
    INIT_ERROR = ["bb3:1", "r:1", "bb3:2"]

    def __init__(self, pin, ticks=4, bpm=120):
        super().__init__(pin, ticks, bpm)
