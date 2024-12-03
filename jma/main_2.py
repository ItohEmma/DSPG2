import flet as ft
import requests
import json

# 気象庁APIのエンドポイント
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

# ローカルJSONファイルのパス
LOCAL_AREA_FILE = "/Users/ema/DSPE/DSPG2/jma/areas.json"

# 天気と対応するアイコンと色
WEATHER_ICONS = {
    "晴れ": (ft.icons.SUNNY, ft.colors.ORANGE),
    "曇り": (ft.icons.CLOUD, ft.colors.GREY),
    "雨": (ft.icons.WATER_DROP, ft.colors.BLUE),
    "雪": (ft.icons.SNOWING, ft.colors.CYAN),
    "雷": (ft.icons.FLASH_ON, ft.colors.YELLOW),
    "曇り時々晴れ": (ft.icons.CLOUD_DONE, ft.colors.LIGHT_BLUE),  # 変更
    "曇り時々雨": (ft.icons.CLOUD_QUEUE, ft.colors.LIGHT_BLUE),
}

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = ft.ScrollMode.AUTO
    page.spacing = 10
    page.padding = 20

    def handle_region_expansion(e):
        """地域選択のExpansionTileの展開/折りたたみ時のハンドラ"""
        page.open(
            ft.SnackBar(
                ft.Text(f"地域リストを{'展開' if e.data=='true' else '折りたたみ'}ました"),
                duration=1000,
            )
        )

    def handle_forecast_expansion(e):
        """天気予報のExpansionTileの展開/折りたたみ時のハンドラ"""
        page.open(
            ft.SnackBar(
                ft.Text(f"天気予報を{'展開' if e.data=='true' else '折りたたみ'}ました"),
                duration=1000,
            )
        )

    # UIコンポーネント
    region_dropdown = ft.Dropdown(
        options=[],
        label="地域を選択してください",
        width=400,
    )

    fetch_button = ft.ElevatedButton(
        "天気予報を取得",
        on_click=lambda e: fetch_forecast(region_dropdown.value),
        disabled=True,
    )

    forecast_result = ft.Column(spacing=10)

    def fetch_regions_from_local():
        """ローカルJSONファイルから地域リストを取得"""
        try:
            with open(LOCAL_AREA_FILE, "r", encoding="utf-8") as file:
                area_data = json.load(file)
                regions = {area_code: area["name"] for area_code, area in area_data["offices"].items()}
                return regions
        except Exception as ex:
            forecast_result.controls.clear()
            forecast_result.controls.append(ft.Text(f"地域リスト取得エラー(ローカル): {ex}", color=ft.colors.RED))
            page.update()
            return None

    def fetch_regions(e):
        """地域リストを取得してUIに更新"""
        regions = fetch_regions_from_local()

        if regions:
            region_dropdown.options = [ft.dropdown.Option(key, name) for key, name in regions.items()]
            region_dropdown.value = None
            fetch_button.disabled = False
            forecast_result.controls.clear()
            forecast_result.controls.append(ft.Text("地域リストを取得しました！", color=ft.colors.GREEN))
            page.update()

    def fetch_forecast(region_code):
        """選択した地域の天気予報を取得"""
        if not region_code:
            forecast_result.controls.clear()
            forecast_result.controls.append(ft.Text("地域を選択してください", color=ft.colors.RED))
            page.update()
            return

        try:
            response = requests.get(FORECAST_URL.format(region_code))
            response.raise_for_status()
            forecast_data = response.json()

            # 天気情報を抽出して表示
            forecast_result.controls.clear()

            time_series = forecast_data[0]["timeSeries"][0]  # 時系列データの最初のセット
            area = time_series["areas"][0]  # 地域データの最初のセット
            dates = time_series["timeDefines"]  # 日付リスト
            weathers = area["weathers"]  # 天気情報リスト

            for date, weather in zip(dates, weathers):
                # アイコンと色を取得、デフォルトは疑問符アイコン
                icon, color = WEATHER_ICONS.get(weather, (ft.icons.HELP, ft.colors.BLACK))
                
                card = ft.Card(
                    content=ft.Container(
                        ft.Column(
                            [
                                ft.Text(date, size=18, weight=ft.FontWeight.BOLD),
                                ft.Icon(icon, size=40, color=color),  # アイコンを使用
                                ft.Text(weather, size=16, color=color),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=10,
                        alignment=ft.alignment.center,
                    ),
                )
                forecast_result.controls.append(card)

        except Exception as ex:
            forecast_result.controls.clear()
            forecast_result.controls.append(ft.Text(f"天気予報取得エラー: {ex}", color=ft.colors.RED))

        page.update()

    # ExpansionTileを使用したUI構築
    page.add(
        ft.Text("天気予報アプリ", size=30, weight=ft.FontWeight.BOLD),
        
        # 地域選択部分のExpansionTile
        ft.ExpansionTile(
            title=ft.Text("地域選択", size=20),
            subtitle=ft.Text("地域リストを取得して天気予報の地域を選択"),
            trailing=ft.Icon(ft.icons.LOCATION_CITY),
            collapsed_text_color=ft.colors.GREEN,
            text_color=ft.colors.GREEN,
            on_change=handle_region_expansion,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.ElevatedButton(
                            "地域リストを取得",
                            on_click=fetch_regions,
                        ),
                        region_dropdown,
                        fetch_button,
                    ], spacing=10),
                    padding=10,
                )
            ],
        ),
        
        # 天気予報結果のExpansionTile
        ft.ExpansionTile(
            title=ft.Text("天気予報", size=20),
            subtitle=ft.Text("選択した地域の天気予報を表示"),
            trailing=ft.Icon(ft.icons.CLOUD),
            collapsed_text_color=ft.colors.BLUE,
            text_color=ft.colors.BLUE,
            on_change=handle_forecast_expansion,
            controls=[
                ft.Container(
                    content=forecast_result,
                    padding=10,
                )
            ],
        )
    )

# アプリケーションを起動
if __name__ == "__main__":
    ft.app(target=main)