import arcade
import arcade.gui
import requests
from io import BytesIO
from PIL import Image

MAPS_API_KEY = ""
GEOCODER_API_KEY = ""


class MapApp(arcade.View):
    def __init__(self):
        super().__init__()
        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        self.ll_x, self.ll_y = 37.6176, 55.7558
        self.spn = 0.005
        self.theme = 'light'
        self.pt = None
        self.map_widget = arcade.gui.UIImage(
            texture=arcade.Texture.create_empty("map", (800, 500)),
            width=800, height=500
        )

        self.setup_ui()
        self.redraw()

    def setup_ui(self):
        self.main_layout = arcade.gui.UIAnchorLayout()

        top_vbox = arcade.gui.UIBoxLayout(vertical=True, space_between=10)
        controls = arcade.gui.UIBoxLayout(vertical=False, space_between=5)

        self.search_input = arcade.gui.UIInputText(text="Москва", width=350, height=30)
        search_btn = arcade.gui.UIFlatButton(text="Искать", width=100)
        reset_btn = arcade.gui.UIFlatButton(text="Сброс", width=80)
        theme_btn = arcade.gui.UIFlatButton(text="Тема", width=80)

        search_btn.on_click = self.perform_search
        reset_btn.on_click = self.reset_search
        theme_btn.on_click = self.toggle_theme

        controls.add(self.search_input)
        controls.add(search_btn)
        controls.add(reset_btn)
        controls.add(theme_btn)

        top_vbox.add(controls)
        top_vbox.add(self.map_widget)

        self.address_label = arcade.gui.UILabel(
            text="Адрес: -",
            width=self.window.width,
            height=40,
            align="center",
            font_size=12
        )

        self.main_layout.add(child=top_vbox, anchor_x="center", anchor_y="top", align_y=-10)
        self.main_layout.add(child=self.address_label, anchor_x="center", anchor_y="bottom")

        self.uimanager.add(self.main_layout)

    def perform_search(self, event=None):
        query = self.search_input.text.strip()
        if not query: return
        try:
            url = "http://geocode-maps.yandex.ru/1.x/?"
            params = {"apikey": GEOCODER_API_KEY, "geocode": query, "format": "json"}
            res = requests.get(url, params=params).json()

            obj = res['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
            self.ll_x, self.ll_y = map(float, obj['Point']['pos'].split())

            full_addr = obj['metaDataProperty']['GeocoderMetaData']['text']
            self.address_label.text = f"Адрес: {full_addr}"

            self.pt = f"{self.ll_x},{self.ll_y},pm2rdm"
            self.redraw()
        except Exception:
            self.address_label.text = "Объект не найден"

    def reset_search(self, event=None):
        self.pt = None
        self.search_input.text = ""
        self.address_label.text = "Адрес: -"
        self.redraw()

    def toggle_theme(self, event):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.redraw()

    def redraw(self):
        try:
            params = {"ll": f"{self.ll_x},{self.ll_y}", "spn": f"{self.spn},{self.spn}",
                      "theme": self.theme, "apikey": MAPS_API_KEY}
            if self.pt: params["pt"] = self.pt

            res = requests.get("https://static-maps.yandex.ru/v1?", params=params)
            res.raise_for_status()
            img = Image.open(BytesIO(res.content)).convert("RGBA")
            self.map_widget.texture = arcade.Texture(img)
        except Exception as e:
            print(f"Update error: {e}")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER: self.perform_search()
        step = self.spn / 2
        if key == arcade.key.PAGEUP:
            self.spn = max(0.0001, self.spn / 2)
            self.redraw()
        elif key == arcade.key.PAGEDOWN:
            self.spn = min(80.0, self.spn * 2)
            self.redraw()
        elif key == arcade.key.LEFT:
            self.ll_x -= step
            self.redraw()
        elif key == arcade.key.RIGHT:
            self.ll_x += step
            self.redraw()
        elif key == arcade.key.UP:
            self.ll_y = min(85.0, self.ll_y + step)
            self.redraw()
        elif key == arcade.key.DOWN:
            self.ll_y = max(-85.0, self.ll_y - step)
            self.redraw()

    def on_draw(self):
        self.clear()
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.window.width / 2, 20, self.window.width, 40),
            (0, 0, 0, 150)
        )
        self.uimanager.draw()


def main():
    arcade.Window(800, 600, "Yandex Maps Search")
    view = MapApp()
    arcade.get_window().show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
