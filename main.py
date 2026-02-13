import arcade
import arcade.gui
import requests
from io import BytesIO
from PIL import Image

SPN = (0.005, 0.005)
apikey = "Enter your API key"


class MainView(arcade.View):
    def __init__(self):
        super().__init__()
        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()
        self.ll_y = '0'
        self.ll_x = '0'
        self.theme = 'light'
        self.map = None
        self.map_widget = arcade.gui.UIImage(
            texture=arcade.Texture.create_empty("start_map", (800, 500)),
            width=800,
            height=500
        )
        self.main_layout = arcade.gui.UIAnchorLayout()
        self.vbox = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        self.menu_layout = arcade.gui.UIGridLayout(
            column_count=3,
            row_count=2,
            horizontal_spacing=15,
            vertical_spacing=10
        )

        label_x = arcade.gui.UILabel(
            text="X:",
            width=100,
            height=30,
            align="right"
        )
        self.input_x = arcade.gui.UIInputText(
            text="",
            width=150,
            height=30,
            caret_color=arcade.color.WHITE,
        )

        label_y = arcade.gui.UILabel(
            text="Y:",
            width=100,
            height=30,
            align="right"
        )
        self.input_y = arcade.gui.UIInputText(
            text="",
            width=150,
            height=30,
            caret_color=arcade.color.WHITE,
        )
        search_button = arcade.gui.UIFlatButton(
            text='Search',
            width=100,
            height=30
        )
        search_button.on_click = self.search_and_draw

        theme_button = arcade.gui.UIFlatButton(
            text='Theme',
            width=100,
            height=30
        )
        theme_button.on_click = self.toggle_theme

        self.menu_layout.add(label_x, column=0, row=0)
        self.menu_layout.add(self.input_x, column=1, row=0)
        self.menu_layout.add(theme_button, column=2, row=0)

        self.menu_layout.add(label_y, column=0, row=1)
        self.menu_layout.add(self.input_y, column=1, row=1)

        self.menu_layout.add(search_button, column=2, row=1)

        self.vbox.add(self.menu_layout)
        self.vbox.add(self.map_widget)
        self.main_layout.add(
            child=self.vbox,
            anchor_x="left",
            anchor_y="top"
        )
        self.uimanager.add(self.main_layout)

    def on_draw(self):
        self.clear()
        self.uimanager.draw()

    def search_and_draw(self, event):
        try:
            global SPN
            SPN = (0.005, 0.005)
            self.ll_x = str(float(self.input_x.text))
            self.ll_y = str(float(self.input_y.text))
            f = requests.get(
                f'https://static-maps.yandex.ru/v1?ll={self.ll_x},{self.ll_y}&spn={str(SPN[0])},{str(SPN[1])}&' +
                f'theme={self.theme}&apikey={apikey}').content
            image = Image.open(BytesIO(f))
            self.map = arcade.Texture(image.convert('RGBA'))
            self.map_widget.texture = self.map
        except Exception:
            print("Invalid input")

    def redraw(self):
        global SPN
        try:
            f = requests.get(
                f'https://static-maps.yandex.ru/v1?ll={self.ll_x},{self.ll_y}&spn={str(SPN[0])},{str(SPN[1])}&' +
                f'theme={self.theme}&apikey={apikey}').content
            image = Image.open(BytesIO(f))
            self.map = arcade.Texture(image.convert('RGBA'))
            self.map_widget.texture = self.map
        except Exception:
            SPN = (80, 80)
            self.ll_x = "0"
            self.ll_y = "0"
            self.input_x.text = "0"
            self.input_y.text = "0"
            self.redraw()

    def toggle_theme(self, event):
        if self.theme == 'light':
            self.theme = 'dark'
        else:
            self.theme = 'light'
        self.redraw()

    def on_key_press(self, key, modifiers):
        global SPN
        if key == arcade.key.PAGEUP:
            if SPN[0] / 5 >= 0.001:
                SPN = (SPN[0] / 5, SPN[1] / 5)
                self.redraw()
        if key == arcade.key.PAGEDOWN:
            if SPN[0] * 5 <= 80:
                SPN = (SPN[0] * 5, SPN[1] * 5)
                self.redraw()
        if key == arcade.key.LEFT:
            self.calculate_x(False)
            self.redraw()
        if key == arcade.key.RIGHT:
            self.calculate_x(True)
            self.redraw()
        if key == arcade.key.UP:
            self.calculate_y(True)
            self.redraw()
        if key == arcade.key.DOWN:
            self.calculate_y(False)
            self.redraw()

    def calculate_x(self, t):
        if t:
            step_x = SPN[0] / 2
            x = float(self.ll_x)
            x += step_x
            x = max(-180.0, min(180.0, x))
            self.ll_x = str(x)
        else:
            step_x = SPN[0] / 2
            x = float(self.ll_x)
            x -= step_x
            x = max(-180.0, min(180.0, x))
            self.ll_x = str(x)

    def calculate_y(self, t):
        if t:
            step_y = SPN[0] / 2
            y = float(self.ll_y)
            y += step_y
            y = max(-180.0, min(180.0, y))
            self.ll_y = str(y)
        else:
            step_y = SPN[0] / 2
            y = float(self.ll_y)
            y -= step_y
            y = max(-180.0, min(180.0, y))
            self.ll_y = str(y)


def main():
    window = arcade.Window(width=800, height=600, title="Map", resizable=True)
    view = MainView()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
