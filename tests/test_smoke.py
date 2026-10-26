"""冒煙測試：確認套件能正常 import。"""


def test_import_board() -> None:
    import board
    import board.comm
    import board.perception
