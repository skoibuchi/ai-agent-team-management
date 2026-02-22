"""
カスタム例外クラス
"""


class HumanInputRequiredException(Exception):
    """
    Human-in-the-Loop機能で人間の入力が必要な場合に発生する例外
    この例外が発生した場合、タスクは一時停止状態になる
    """
    def __init__(self, message: str = "Human input required"):
        self.message = message
        super().__init__(self.message)


class TaskCancelledException(Exception):
    """
    タスクがキャンセルされた場合に発生する例外
    """
    def __init__(self, message: str = "Task was cancelled"):
        self.message = message
        super().__init__(self.message)
