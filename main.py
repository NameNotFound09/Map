import arcade
import arcade.gui
import requests
from io import BytesIO
from PIL import Image
import math

MAPS_API_KEY = ""
GEOCODER_API_KEY = ""
SEARCH_API_KEY = ""


class MapApp(arcade.View):
    def __init__(self):
        super().__init__()
        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()

        self.ll_x, self.ll_y = 37.6176, 55.7558
        self.spn = 0.005
        self.theme = 'light'
        self.pt = None
        self.use_postal_code = False
        self.last_geo_object = None

        self.req_w, self.req_h = 600, 450

        self.map_widget = arcade.gui.UIImage(
            texture=arcade.Texture.create_empty("map", (self.req_w, self.req_h)),
            width=self.req_w, height=self.req_h
        )

        self.setup_ui()
        self.redraw()

    def setup_ui(self):
        self.main_layout = arcade.gui.UIAnchorLayout()
        top_vbox = arcade.gui.UIBoxLayout(vertical=True, space_between=10)
        controls = arcade.gui.UIBoxLayout(vertical=False, space_between=5)

        self.search_input = arcade.gui.UIInputText(text="Москва", width=200, height=30)
        search_btn = arcade.gui.UIFlatButton(text="Искать", width=80)
        reset_btn = arcade.gui.UIFlatButton(text="Сброс", width=70)
        theme_btn = arcade.gui.UIFlatButton(text="Тема", width=70)
        self.index_btn = arcade.gui.UIFlatButton(text="Индекс: Выкл", width=120)

        search_btn.on_click = self.perform_search
        reset_btn.on_click = self.reset_search
        theme_btn.on_click = self.toggle_theme
        self.index_btn.on_click = self.toggle_postal_code

        controls.add(self.search_input)
        controls.add(search_btn)
        controls.add(reset_btn)
        controls.add(theme_btn)
        controls.add(self.index_btn)

        top_vbox.add(controls)
        top_vbox.add(self.map_widget)

        self.address_label = arcade.gui.UILabel(
            text="Адрес: -", width=self.window.width, height=40, align="center", font_size=12
        )

        self.main_layout.add(child=top_vbox, anchor_x="center", anchor_y="top", align_y=-10)
        self.main_layout.add(child=self.address_label, anchor_x="center", anchor_y="bottom")
        self.uimanager.add(self.main_layout)

    def lonlat_distance(self, a, b):
        degree_to_meters_factor = 111 * 1000
        a_lon, a_lat = a
        b_lon, b_lat = b
        radians_lattitude = math.radians((a_lat + b_lat) / 2.)
        lat_distance = abs(a_lat - b_lat) * degree_to_meters_factor
        lon_distance = abs(a_lon - b_lon) * degree_to_meters_factor * math.cos(radians_lattitude)
        distance = math.sqrt(lat_distance * lat_distance + lon_distance * lon_distance)
        return distance

    def update_address_text(self):
        if not self.last_geo_object: return
        meta = self.last_geo_object['metaDataProperty']['GeocoderMetaData']
        address = meta['text']
        if self.use_postal_code:
            postal_code = meta.get('Address', {}).get('postal_code')
            address = f"{postal_code}, {address}" if postal_code else f"[Нет индекса], {address}"
        self.address_label.text = f"Адрес: {address}"

    def reverse_geocode(self, lon, lat):
        try:
            url = "http://geocode-maps.yandex.ru/1.x/?"
            params = {"apikey": GEOCODER_API_KEY, "geocode": f"{lon},{lat}", "format": "json"}
            res = requests.get(url, params=params).json()
            self.last_geo_object = res['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
            self.pt = f"{lon},{lat},pm2rdm"
            self.update_address_text()
            self.redraw()
        except Exception:
            self.address_label.text = "Объект не найден"

    def find_organization(self, lon, lat):
        try:
            url = "https://search-maps.yandex.ru/v1/"
            params = {
                "apikey": SEARCH_API_KEY,
                "text": "организация",
                "ll": f"{lon},{lat}",
                "type": "biz",
                "lang": "ru_RU",
                "results": 1
            }
            res = requests.get(url, params=params).json()

            if not res.get("features"):
                self.address_label.text = "Организаций рядом не найдено"
                return

            org = res["features"][0]
            org_lon, org_lat = org["geometry"]["coordinates"]

            dist = self.lonlat_distance((lon, lat), (org_lon, org_lat))

            if dist <= 50:
                name = org["properties"]["CompanyMetaData"]["name"]
                addr = org["properties"]["CompanyMetaData"].get("address", "Адрес не указан")
                self.address_label.text = f"Орг: {name} | {addr} ({int(dist)}м)"
                self.pt = f"{org_lon},{org_lat},pm2rdm"
                self.last_geo_object = None
                self.redraw()
            else:
                self.address_label.text = f"Ближайшая орг. слишком далеко ({int(dist)}м)"
        except Exception:
            self.address_label.text = "Ошибка поиска организаций"

    def perform_search(self, event=None):
        query = self.search_input.text.strip()
        if not query: return
        try:
            url = "http://geocode-maps.yandex.ru/1.x/?"
            params = {"apikey": GEOCODER_API_KEY, "geocode": query, "format": "json"}
            res = requests.get(url, params=params).json()
            self.last_geo_object = res['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
            self.ll_x, self.ll_y = map(float, self.last_geo_object['Point']['pos'].split())
            self.pt = f"{self.ll_x},{self.ll_y},pm2rdm"
            self.update_address_text()
            self.redraw()
        except Exception:
            self.address_label.text = "Объект не найден"

    def on_mouse_press(self, x, y, button, modifiers):
        m = self.map_widget
        if (m.center_x - m.width / 2 < x < m.center_x + m.width / 2 and
                m.center_y - m.height / 2 < y < m.center_y + m.height / 2):

            dx = x - m.center_x
            dy = y - m.center_y
            click_lon = self.ll_x + (dx / m.width) * self.spn * 2.0
            click_lat = self.ll_y + (dy / m.height) * self.spn * 1.2

            if button == arcade.MOUSE_BUTTON_LEFT:
                self.reverse_geocode(click_lon, click_lat)
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                self.find_organization(click_lon, click_lat)

    def reset_search(self, event=None):
        self.pt = None
        self.last_geo_object = None
        self.search_input.text = ""
        self.address_label.text = "Адрес: -"
        self.redraw()

    def toggle_theme(self, event):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.redraw()

    def toggle_postal_code(self, event):
        self.use_postal_code = not self.use_postal_code
        self.index_btn.text = f"Индекс: {'Вкл' if self.use_postal_code else 'Выкл'}"
        self.update_address_text()

    def redraw(self):
        try:
            params = {"ll": f"{self.ll_x},{self.ll_y}", "spn": f"{self.spn},{self.spn}",
                      "size": f"{self.req_w},{self.req_h}", "theme": self.theme, "apikey": MAPS_API_KEY}
            if self.pt: params["pt"] = self.pt
            res = requests.get("https://static-maps.yandex.ru/v1?", params=params)
            res.raise_for_status()
            img = Image.open(BytesIO(res.content)).convert("RGBA")
            self.map_widget.texture = arcade.Texture(img)
        except Exception as e:
            print(f"Error: {e}")

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
        arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width / 2, 20, self.window.width, 40), (0, 0, 0, 150))
        self.uimanager.draw()


def main():
    window = arcade.Window(800, 600, "Yandex Maps Search")
    view = MapApp()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
