import flet as ft


def main(page:ft.Page):
    #アプリ名を設定
    page.title = "Hello, Flet!"
    page.add(ft.SafeArea(ft.Text("Hello, Flet!")))
    
    page.add(ft.FilledButton("Click me!"))
ft.app(main)