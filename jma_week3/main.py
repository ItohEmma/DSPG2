import flet as ft
import requests
import json
import sqlite3
from datetime import datetime

# 気象庁APIのエンドポイント
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

# ローカルJSONファイルのパス
LOCAL_AREA_FILE = "/Users/ema/DSPE/DSPG2/jma/areas.json"

# データベース名
DB_NAME = "weather_forecast.db"

# 天気と対応するアイコンと色
WEATHER_ICONS = {
    "晴れ": (ft.icons.SUNNY, ft.colors.ORANGE),
    "曇り": (ft.icons.CLOUD, ft.colors.GREY),
    "雨": (ft.icons.WATER_DROP, ft.colors.BLUE),
    "雪": (ft.icons.AC_UNIT, ft.colors.CYAN),
    "雷": (ft.icons.FLASH_ON, ft.colors.YELLOW),
    "曇り時々晴れ": (ft.icons.CLOUD_QUEUE, ft.colors.LIGHT_BLUE),
    "晴れ時々曇り": (ft.icons.CLOUD_QUEUE, ft.colors.ORANGE),
    "曇り時々雨": (ft.icons.CLOUD_QUEUE, ft.colors.BLUE),
    "雨時々曇り": (ft.icons.CLOUD_QUEUE, ft.colors.BLUE),
    "晴れのち曇り": (ft.icons.CLOUD, ft.colors.LIGHT_BLUE),
    "曇りのち晴れ": (ft.icons.SUNNY, ft.colors.ORANGE),
    "曇りのち雨": (ft.icons.WATER_DROP, ft.colors.BLUE),
    "雨のち曇り": (ft.icons.CLOUD, ft.colors.GREY),
    "所により曇り": (ft.icons.CLOUD_QUEUE, ft.colors.GREY),
    "所により雨": (ft.icons.WATER_DROP, ft.colors.BLUE),
    "所により雪": (ft.icons.AC_UNIT, ft.colors.CYAN),
}

class WeatherDB:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """データベースの初期化"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 地域マスターテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 天気予報テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region_code TEXT,
                    forecast_date TEXT,
                    weather TEXT,
                    temperature_min REAL,
                    temperature_max REAL,
                    rainfall_probability INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (region_code) REFERENCES regions (code)
                )
            """)
            
            # お気に入り地域テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorite_regions (
                    region_code TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (region_code) REFERENCES regions (code)
                )
            """)

    def clear_old_forecasts(self):
        """古い天気予報データを削除"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM forecasts 
                WHERE created_at < datetime('now', '-1 day')
            """)

def get_weather_icon(weather_str):
    # 完全一致で検索
    if weather_str in WEATHER_ICONS:
        return WEATHER_ICONS[weather_str]
    
    # 部分一致で検索
    for key in WEATHER_ICONS:
        if key in weather_str:
            return WEATHER_ICONS[key]
    
    # 該当なしの場合はデフォルト値を返す
    return (ft.icons.HELP, ft.colors.BLACK)

def migrate_regions_to_db():
    """JSONファイルから地域データをDBに移行"""
    try:
        # JSONファイルの読み込み
        with open(LOCAL_AREA_FILE, "r", encoding="utf-8") as file:
            area_data = json.load(file)
        
        # データベースに接続
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 既存のデータを削除
        cursor.execute("DELETE FROM regions")
        
        # 新しいデータを挿入
        for area_code, area in area_data["offices"].items():
            cursor.execute(
                "INSERT INTO regions (code, name) VALUES (?, ?)",
                (area_code, area["name"])
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as ex:
        print(f"データ移行エラー: {ex}")
        return False

def get_regions_from_db():
    """データベースから地域リストを取得"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT code, name FROM regions ORDER BY name")
        regions = dict(cursor.fetchall())
        conn.close()
        return regions
    except Exception as ex:
        print(f"地域データ取得エラー: {ex}")
        return None

def save_forecast_to_db(region_code, forecasts):
    """天気予報データをDBに保存"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        for date, weather in forecasts:
            cursor.execute("""
                INSERT INTO forecasts (region_code, forecast_date, weather)
                VALUES (?, ?, ?)
            """, (region_code, date, weather))
        
        conn.commit()
        conn.close()
        return True
    except Exception as ex:
        print(f"天気予報保存エラー: {ex}")
        return False

def get_latest_forecast_from_db(region_code):
    """指定地域の最新の天気予報をDBから取得"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT forecast_date, weather
            FROM forecasts
            WHERE region_code = ?
            AND created_at >= datetime('now', '-1 hour')
            ORDER BY created_at DESC
        """, (region_code,))
        forecasts = cursor.fetchall()
        conn.close()
        return forecasts if forecasts else None
    except Exception as ex:
        print(f"天気予報取得エラー: {ex}")
        return None

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = ft.ScrollMode.AUTO
    page.spacing = 10
    page.padding = 20

    weather_db = WeatherDB()

    def handle_region_expansion(e):
        """地域選択のExpansionTileの展開/折りたたみ時のハンドラ"""
        page.show_snack_

    def handle_region_expansion(e):
        """地域選択のExpansionTileの展開/折りたたみ時のハンドラ"""
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"地域リストを{'展開' if e.data=='true' else '折りたたみ'}ました"),
                duration=1000,
            )
        )

    def handle_forecast_expansion(e):
        """天気予報のExpansionTileの展開/折りたたみ時のハンドラ"""
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"天気予報を{'展開' if e.data=='true' else '折りたたみ'}ました"),
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
    favorite_regions = ft.Column(spacing=10)

    def fetch_regions(e):
        """地域リストを取得してUIに更新（DB版）"""
        # DBの初期化
        weather_db.init_database()
        
        # 初回のみJSONからDBへの移行を実行
        migrate_regions_to_db()
        
        # DBから地域リストを取得
        regions = get_regions_from_db()
        
        if regions:
            region_dropdown.options = [
                ft.dropdown.Option(key, name) for key, name in regions.items()
            ]
            region_dropdown.value = None
            fetch_button.disabled = False
            forecast_result.controls.clear()
            forecast_result.controls.append(
                ft.Text("地域リストを取得しました！", color=ft.colors.GREEN)
            )
            page.update()

    def display_forecasts(forecasts):
        """天気予報の表示処理"""
        forecast_result.controls.clear()
        
        for date, weather in forecasts:
            icon, color = get_weather_icon(weather)
            
            card = ft.Card(
                content=ft.Container(
                    ft.Column(
                        [
                            ft.Text(date, size=18, weight=ft.FontWeight.BOLD),
                            ft.Icon(icon, size=40, color=color),
                            ft.Text(weather, size=16, color=color),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    padding=10,
                    alignment=ft.alignment.center,
                )
            )
            forecast_result.controls.append(card)
        
        page.update()

    def fetch_forecast(region_code):
        """天気予報を取得（DB対応版）"""
        if not region_code:
            forecast_result.controls.clear()
            forecast_result.controls.append(
                ft.Text("地域を選択してください", color=ft.colors.RED)
            )
            page.update()
            return

        try:
            # まずDBから最新の予報を確認
            cached_forecasts = get_latest_forecast_from_db(region_code)
            
            if cached_forecasts:
                # キャッシュされた予報を表示
                display_forecasts(cached_forecasts)
            else:
                # APIから新しい予報を取得
                response = requests.get(FORECAST_URL.format(region_code))
                response.raise_for_status()
                forecast_data = response.json()

                time_series = forecast_data[0]["timeSeries"][0]
                area = time_series["areas"][0]
                dates = time_series["timeDefines"]
                weathers = area["weathers"]

                # 予報データをDBに保存
                forecasts = list(zip(dates, weathers))
                save_forecast_to_db(region_code, forecasts)
                
                # 予報を表示
                display_forecasts(forecasts)

        except Exception as ex:
            forecast_result.controls.clear()
            forecast_result.controls.append(
                ft.Text(f"天気予報取得エラー: {ex}", color=ft.colors.RED)
            )
            page.update()

    def add_to_favorites(e):
        """選択した地域をお気に入りに追加"""
        if not region_dropdown.value:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("地域を選択してください"))
            )
            return
            
        try:
            with weather_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO favorite_regions (region_code) VALUES (?)",
                    (region_dropdown.value,)
                )
            update_favorite_list()
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("お気に入りに追加しました"))
            )
        except Exception as ex:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"エラー: {ex}"))
            )

    def remove_from_favorites(region_code):
        """お気に入りから地域を削除"""
        try:
            with weather_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM favorite_regions WHERE region_code = ?",
                    (region_code,)
                )
            update_favorite_list()
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("お気に入りから削除しました"))
            )
        except Exception as ex:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"エラー: {ex}"))
            )

    def update_favorite_list():
        """お気に入り地域リストを更新"""
        favorite_regions.controls.clear()
        
        try:
            with weather_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.code, r.name 
                    FROM favorite_regions f
                    JOIN regions r ON f.region_code = r.code
                    ORDER BY r.name
                """)
                favorites = cursor.fetchall()
                
                for code, name in favorites:
                    favorite_regions.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.FAVORITE, color=ft.colors.RED),
                            title=ft.Text(name),
                            trailing=ft.IconButton(
                                ft.icons.DELETE,
                                on_click=lambda e, c=code: remove_from_favorites(c)
                            ),
                            on_click=lambda e, c=code: fetch_forecast(c)
                        )
                    )
        except Exception as ex:
            favorite_regions.controls.append(
                ft.Text(f"お気に入りの取得に失敗: {ex}", color=ft.colors.RED)
            )
        
        page.update()

    # UIの構築
    def main(page: ft.Page):
        page.title = "天気予報アプリ"
        page.scroll = ft.ScrollMode.AUTO
        page.spacing = 10
        page.padding = 20

        weather_db = WeatherDB()

        def handle_region_expansion(e):
            """地域選択のExpansionTileの展開/折りたたみ時のハンドラ"""
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"地域リストを{'展開' if e.data=='true' else '折りたたみ'}ました"),
                    duration=1000,
                )
            )

    # 以下、前回のコードと同じ...
        # 地域選択部分
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

        # UIの構築
    page.add(
        ft.Text("天気予報アプリ", size=30, weight=ft.FontWeight.BOLD),
        
        # 地域選択部分
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
        
        # お気に入り部分
        ft.ExpansionTile(
            title=ft.Text("お気に入り地域", size=20),
            subtitle=ft.Text("よく確認する地域をお気に入りとして保存"),
            trailing=ft.Icon(ft.icons.FAVORITE),
            collapsed_text_color=ft.colors.RED,
            text_color=ft.colors.RED,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.ElevatedButton(
                            "現在の地域をお気に入りに追加",
                            on_click=add_to_favorites,
                            icon=ft.icons.ADD
                        ),
                        favorite_regions
                    ]),
                    padding=10
                )
            ]
        ),
        
        # 天気予報結果部分
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

    # 初期化時にお気に入りリストを更新
    update_favorite_list()

# アプリケーションの起動
if __name__ == "__main__":
    ft.app(target=main)