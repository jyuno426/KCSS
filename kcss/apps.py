from django.apps import AppConfig


class KcssConfig(AppConfig):
    name = "kcss"
    title = "Korean Computer Scientist Search (KCSS)"
    author = "Junho Han, Seunghyun Lee, Jinwoo Shin"
    canvas_height = {10: "400px", 25: "600px", 50: "900px", 100: "1100px"}
