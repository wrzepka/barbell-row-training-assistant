from enum import IntEnum


class Screen(IntEnum):
    """
    Enumerator z identyfikatorami widoków QStackedWidget
    """

    LOBBY = 0
    TRAINING = 1
    HISTORY = 2

class ScreenModes(IntEnum):
    """
    Enumerator z identyfikatorami trybów każdego z widoków QStackedWidget.
    Każdy widok składa się z szkieletu (używanego podczas ładowania widoku) i realnego widoku.
    """

    SKELETON = 0
    REAL = 1

# Minimalna długość ładowania widoku szkieletowego i loading screenu
SKELETON_MINIMAL_DELAY = 400 # 400ms to optymalna długość, aby ludzkie oko zarejestrowało szkielet.
LOADING_SCREEN_MINIMAL_DELAY = 200