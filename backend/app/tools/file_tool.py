"""
ファイル操作ツール（LangChain標準）
"""
from typing import Type
import os
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class FileReadInput(BaseModel):
    """ファイル読み込みツールの入力スキーマ"""
    file_path: str = Field(description="読み込むファイルのパス")
    encoding: str = Field(
        default="utf-8",
        description="ファイルのエンコーディング"
    )


class FileReadTool(BaseTool):
    """
    ファイル読み込みツール
    
    指定されたファイルの内容を読み込みます。
    テキストファイル、設定ファイル、ログファイルなどの読み込みに使用します。
    """
    
    name: str = "read_file"
    description: str = (
        "ファイルの内容を読み込みます。"
        "テキストファイル、設定ファイル、ログファイルなどを読む際に使用してください。"
        "ファイルパスとエンコーディングを指定できます。"
    )
    args_schema: Type[BaseModel] = FileReadInput
    
    def _run(self, file_path: str, encoding: str = "utf-8") -> str:
        """
        ファイルを読み込む（同期版）
        
        Args:
            file_path: ファイルパス
            encoding: エンコーディング
            
        Returns:
            str: ファイルの内容
        """
        try:
            # セキュリティ: パストラバーサル攻撃を防ぐ
            file_path = os.path.abspath(file_path)
            
            # ファイルの存在確認
            if not os.path.exists(file_path):
                return f"エラー: ファイルが見つかりません - {file_path}"
            
            # ファイルを読み込む
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return f"ファイル: {file_path}\nサイズ: {len(content)} 文字\n\n内容:\n{content}"
            
        except Exception as e:
            return f"エラー: ファイルの読み込みに失敗しました - {str(e)}"
    
    async def _arun(self, file_path: str, encoding: str = "utf-8") -> str:
        """ファイルを読み込む（非同期版）"""
        return self._run(file_path, encoding)


class FileWriteInput(BaseModel):
    """ファイル書き込みツールの入力スキーマ"""
    file_path: str = Field(description="書き込むファイルのパス")
    content: str = Field(description="書き込む内容")
    encoding: str = Field(
        default="utf-8",
        description="ファイルのエンコーディング"
    )
    mode: str = Field(
        default="write",
        description="書き込みモード: 'write'（上書き）または 'append'（追記）"
    )


class FileWriteTool(BaseTool):
    """
    ファイル書き込みツール
    
    指定されたファイルに内容を書き込みます。
    レポート作成、ログ記録、データ保存などに使用します。
    """
    
    name: str = "write_file"
    description: str = (
        "ファイルに内容を書き込みます。"
        "レポート作成、ログ記録、データ保存などに使用してください。"
        "上書きモードと追記モードを選択できます。"
    )
    args_schema: Type[BaseModel] = FileWriteInput
    
    def _run(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        mode: str = "write"
    ) -> str:
        """
        ファイルに書き込む（同期版）
        
        Args:
            file_path: ファイルパス
            content: 書き込む内容
            encoding: エンコーディング
            mode: 書き込みモード
            
        Returns:
            str: 実行結果
        """
        try:
            # セキュリティ: パストラバーサル攻撃を防ぐ
            file_path = os.path.abspath(file_path)
            
            # ディレクトリが存在しない場合は作成
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # ファイルに書き込む
            write_mode = 'a' if mode == 'append' else 'w'
            with open(file_path, write_mode, encoding=encoding) as f:
                f.write(content)
            
            bytes_written = len(content.encode(encoding))
            mode_text = "追記" if mode == "append" else "上書き"
            
            return (
                f"成功: ファイルに{mode_text}しました\n"
                f"ファイル: {file_path}\n"
                f"書き込みバイト数: {bytes_written}"
            )
            
        except Exception as e:
            return f"エラー: ファイルの書き込みに失敗しました - {str(e)}"
    
    async def _arun(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        mode: str = "write"
    ) -> str:
        """ファイルに書き込む（非同期版）"""
        return self._run(file_path, content, encoding, mode)


class FileListInput(BaseModel):
    """ファイル一覧ツールの入力スキーマ"""
    directory: str = Field(description="一覧を取得するディレクトリパス")
    pattern: str = Field(
        default="*",
        description="ファイルパターン（例: '*.txt', '*.py'）"
    )
    recursive: bool = Field(
        default=False,
        description="サブディレクトリも含めるかどうか"
    )


class FileListTool(BaseTool):
    """
    ファイル一覧取得ツール
    
    指定されたディレクトリ内のファイルとディレクトリを一覧表示します。
    プロジェクト構造の確認、ファイル検索などに使用します。
    """
    
    name: str = "list_files"
    description: str = (
        "ディレクトリ内のファイルとディレクトリを一覧表示します。"
        "プロジェクト構造の確認、特定のファイルの検索などに使用してください。"
        "パターンマッチングと再帰的な検索に対応しています。"
    )
    args_schema: Type[BaseModel] = FileListInput
    
    def _run(
        self,
        directory: str,
        pattern: str = "*",
        recursive: bool = False
    ) -> str:
        """
        ファイル一覧を取得（同期版）
        
        Args:
            directory: ディレクトリパス
            pattern: ファイルパターン
            recursive: 再帰的に検索するか
            
        Returns:
            str: ファイル一覧
        """
        try:
            # セキュリティ: パストラバーサル攻撃を防ぐ
            directory = os.path.abspath(directory)
            
            # ディレクトリの存在確認
            if not os.path.exists(directory):
                return f"エラー: ディレクトリが見つかりません - {directory}"
            
            if not os.path.isdir(directory):
                return f"エラー: ディレクトリではありません - {directory}"
            
            # ファイル一覧を取得
            path_obj = Path(directory)
            if recursive:
                files = list(path_obj.rglob(pattern))
            else:
                files = list(path_obj.glob(pattern))
            
            # 結果を整形
            output = f"ディレクトリ: {directory}\n"
            output += f"パターン: {pattern}\n"
            output += f"再帰的: {'はい' if recursive else 'いいえ'}\n"
            output += f"見つかったファイル数: {len(files)}\n\n"
            
            for file in files:
                file_type = "📁" if file.is_dir() else "📄"
                size = f" ({file.stat().st_size} bytes)" if file.is_file() else ""
                output += f"{file_type} {file.name}{size}\n"
                output += f"   パス: {file}\n"
            
            return output
            
        except Exception as e:
            return f"エラー: ファイル一覧の取得に失敗しました - {str(e)}"
    
    async def _arun(
        self,
        directory: str,
        pattern: str = "*",
        recursive: bool = False
    ) -> str:
        """ファイル一覧を取得（非同期版）"""
        return self._run(directory, pattern, recursive)
