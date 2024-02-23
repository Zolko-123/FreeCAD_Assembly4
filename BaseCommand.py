class BaseCommand():
    """Base class to prepare all the commands."""

    def __init__(self):
        pass

    def Activated(self):
        pass

    def GetResources(self):
        return {
            "Pixmap": self.pixmap,
            "MenuText": self.menutext,
            "ToolTip": self.tooltip,
        }

