"""
Theme model for the Money application.
"""

from bson import ObjectId

class Theme:
    """Represents a visual theme for the application."""

    def __init__(
        self,
        _id: ObjectId = None,
        window_bg: str = "#1e1e1e",
        text_color: str = "#ffffff",

        button_bg: str = "#000000",
        button_fg: str = "#ffffff",
        button_border: str = "#007ACC",

        button_hover_bg: str = "#5A5A5A",
        button_hover_border: str = "#0096FF",

        button_pressed_bg: str = "#2F2F2F",
        button_pressed_border: str = "#005699",

        button_disabled_bg: str = "#303030",
        button_disabled_fg: str = "#808080",
        button_disabled_border: str = "#404040",

        tab_selected_bg: str = "#0078d7",
        tab_selected_fg: str = "#ffffff",

        font_family: str = "Segoe UI",
        font_size: str = "18px",

        header_tab_bg: str = "#1e1e1e",
        header_tab_fg: str = "#ffffff",
        header_tab_border: str = "#ffffff",

        positive_color: str = "#2ecc71",
        negative_color: str = "#e74c3c",

        line_color: str = "#636efa",

        row_selected_bg = "#3874f2",
        row_selected_fg = "#ffffff",

        odd_line_bg = "#4d4d4d",

        account_list_border = "#ffffff"
    ):
        self._id = _id

        # Global
        self.window_bg = window_bg
        self.text_color = text_color

        # Buttons
        self.button_bg = button_bg
        self.button_fg = button_fg
        self.button_border = button_border

        self.button_hover_bg = button_hover_bg
        self.button_hover_border = button_hover_border

        self.button_pressed_bg = button_pressed_bg
        self.button_pressed_border = button_pressed_border

        self.button_disabled_bg = button_disabled_bg
        self.button_disabled_fg = button_disabled_fg
        self.button_disabled_border = button_disabled_border

        # Tabs
        self.tab_selected_bg = tab_selected_bg
        self.tab_selected_fg = tab_selected_fg

        # Fonts
        self.font_family = font_family
        self.font_size = font_size

        self.header_tab_bg = header_tab_bg
        self.header_tab_fg = header_tab_fg
        self.header_tab_border = header_tab_border

        self.positive_color = positive_color
        self.negative_color = negative_color

        self.line_color = line_color

        self.row_selected_bg = row_selected_bg
        self.row_selected_fg = row_selected_fg

        self.odd_line_bg = odd_line_bg

        self.account_list_border = account_list_border

    def to_dict(self):
        """Convert theme to a dictionary for database storage."""
        return {
            "_id": self._id,
            "window_bg": self.window_bg,
            "text_color": self.text_color,

            "button_bg": self.button_bg,
            "button_fg": self.button_fg,
            "button_border": self.button_border,

            "button_hover_bg": self.button_hover_bg,
            "button_hover_border": self.button_hover_border,

            "button_pressed_bg": self.button_pressed_bg,
            "button_pressed_border": self.button_pressed_border,

            "button_disabled_bg": self.button_disabled_bg,
            "button_disabled_fg": self.button_disabled_fg,
            "button_disabled_border": self.button_disabled_border,

            "tab_selected_bg": self.tab_selected_bg,
            "tab_selected_fg": self.tab_selected_fg,

            "font_family": self.font_family,
            "font_size": self.font_size,

            "header_tab_bg": self.header_tab_bg,
            "header_tab_fg": self.header_tab_fg,
            "header_tab_border": self.header_tab_border,

            "positive_color": self.positive_color,
            "negative_color": self.negative_color,

            "line_color" : self.line_color,

            "row_selecteg_bg" : self.row_selected_bg,
            "row_selecteg_fg" : self.row_selected_fg,
            
            "odd_line_bg" : self.odd_line_bg,

            "account_list_border" : self.account_list_border

        }
