"""
AIを使用した動的ツール生成
"""
import json
import re
import sys
import subprocess
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel


class DynamicToolGenerator:
    """
    AIを使用して動的にツールを生成
    
    ユーザーの自然言語の説明から、LangChain標準のツールを自動生成します。
    """
    
    def __init__(self, llm: BaseChatModel):
        """
        Args:
            llm: ツール生成に使用するLLM
        """
        self.llm = llm
    
    async def generate_tool_from_description(
        self,
        description: str,
        user_requirements: Optional[Dict[str, Any]] = None
    ) -> tuple[BaseTool, str]:
        """
        自然言語の説明からツールを生成
        
        Args:
            description: ツールの説明（自然言語）
            user_requirements: 追加要件
            
        Returns:
            tuple[BaseTool, str]: (生成されたツール, 生成されたコード)
        """
        # Step 1: AIにツール仕様を生成させる
        tool_spec = await self._generate_tool_spec(description, user_requirements)
        
        # Step 2: AIにPythonコードを生成させる
        tool_code = await self._generate_tool_code(tool_spec)
        
        # Step 3: コードを検証
        is_valid, error = self._validate_code(tool_code)
        if not is_valid:
            raise ValueError(f"Generated code is invalid: {error}")
        
        # Step 4: DynamicToolを作成
        dynamic_tool = self._create_dynamic_tool(tool_spec, tool_code)
        
        return dynamic_tool, tool_code
    
    async def _generate_tool_spec(
        self,
        description: str,
        user_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """ツール仕様を生成"""
        prompt = f"""あなたはツール設計の専門家です。以下の説明から、LangChain標準ツールの仕様を生成してください。

ユーザーの説明:
{description}

追加要件:
{json.dumps(user_requirements or {}, ensure_ascii=False)}

以下のJSON形式で仕様を出力してください（JSONのみ、説明不要）:
{{
    "name": "ツール名（snake_case、英語）",
    "description": "ツールの説明（日本語可）",
    "category": "カテゴリ（research/file_operations/api/code/custom）",
    "parameters": [
        {{
            "name": "パラメータ名",
            "type": "string/number/boolean",
            "description": "パラメータの説明",
            "required": true,
            "default": null
        }}
    ],
    "returns": "戻り値の説明",
    "dependencies": ["必要なPythonパッケージ（標準ライブラリ以外）"],
    "implementation_notes": "実装時の注意点"
}}"""
        
        response = await self.llm.ainvoke(prompt)
        content = response.content
        
        # JSONを抽出
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            tool_spec = json.loads(json_match.group())
        else:
            tool_spec = json.loads(content)
        
        return tool_spec
    
    async def _generate_tool_code(self, tool_spec: Dict[str, Any]) -> str:
        """ツールのPythonコードを生成"""
        prompt = f"""以下のツール仕様に基づいて、LangChain標準のBaseToolを継承したPythonクラスを生成してください。

ツール仕様:
{json.dumps(tool_spec, indent=2, ensure_ascii=False)}

要件:
1. langchain_core.tools.BaseToolを継承
2. name, description, args_schemaを定義
3. Pydanticでargs_schemaを定義
4. _run()メソッドを実装（実際に動作するコード）
5. エラーハンドリングを含める
6. 戻り値は文字列（str）
7. 危険な操作（eval, exec, os.system等）は使用しない
8. 外部APIを使う場合はrequestsライブラリを使用

Pythonコードのみを出力してください（```pythonなどのマークダウン記法不要）:
"""
        
        response = await self.llm.ainvoke(prompt)
        tool_code = response.content
        
        # マークダウンのコードブロックを削除
        tool_code = re.sub(r'```python\n?', '', tool_code)
        tool_code = re.sub(r'```\n?', '', tool_code)
        tool_code = tool_code.strip()
        
        return tool_code
    
    def _validate_code(self, code: str) -> tuple[bool, str]:
        """生成されたコードを検証"""
        try:
            # 構文チェック
            compile(code, '<string>', 'exec')
            
            # 危険なコードのチェック
            dangerous_patterns = [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'__import__',
                r'os\.system',
                r'subprocess\.call',
                r'subprocess\.run',
                r'subprocess\.Popen',
                r'\bopen\s*\([^)]*["\']w',  # ファイル書き込み
                r'rm\s+-rf',
                r'del\s+',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code):
                    return False, f"Dangerous pattern detected: {pattern}"
            
            # 必須要素のチェック
            if 'class' not in code:
                return False, "No class definition found"
            
            if 'BaseTool' not in code:
                return False, "Class must inherit from BaseTool"
            
            if 'def _run' not in code:
                return False, "_run method not found"
            
            return True, ""
            
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _extract_imports(self, code: str) -> List[str]:
        """
        コードからimportステートメントを抽出
        
        Args:
            code: Pythonコード
            
        Returns:
            List[str]: インポートされるモジュール名のリスト
        """
        imports = []
        
        # import xxx
        imports.extend(re.findall(r'^\s*import\s+(\w+)', code, re.MULTILINE))
        
        # from xxx import yyy
        imports.extend(re.findall(r'^\s*from\s+(\w+)', code, re.MULTILINE))
        
        return list(set(imports))
    
    def _is_stdlib_module(self, module_name: str) -> bool:
        """
        標準ライブラリのモジュールかチェック
        
        Args:
            module_name: モジュール名
            
        Returns:
            bool: 標準ライブラリの場合True
        """
        stdlib_modules = {
            'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
            'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
            'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
            'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
            'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
            'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
            'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
            'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
            'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp',
            'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
            'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
            'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
            'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
            'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse',
            'os', 'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
            'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
            'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue',
            'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter',
            'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
            'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
            'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
            'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
            'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
            'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata',
            'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
            'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp',
            'zipfile', 'zipimport', 'zlib', '_thread'
        }
        return module_name in stdlib_modules
    
    def _install_missing_modules(self, modules: List[str]) -> None:
        """
        不足しているモジュールを自動インストール
        
        Args:
            modules: モジュール名のリスト
        """
        for module in modules:
            # 標準ライブラリはスキップ
            if self._is_stdlib_module(module):
                continue
            
            # 既にインストール済みかチェック
            try:
                __import__(module)
                continue
            except ImportError:
                pass
            
            # venv内のpipを使用してインストール
            print(f"Installing missing module: {module}")
            try:
                # sys.executableは現在のPythonインタープリタのパス（venv内）
                subprocess.check_call(
                    [sys.executable, '-m', 'pip', 'install', module],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"Successfully installed: {module}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {module}: {e}")
                raise ValueError(f"Failed to install required module: {module}")
    
    def _create_dynamic_tool(
        self,
        tool_spec: Dict[str, Any] | None,
        tool_code: str
    ) -> BaseTool:
        """
        DynamicToolインスタンスを作成
        
        Args:
            tool_spec: ツール仕様（オプション）
            tool_code: ツールのPythonコード
            
        Returns:
            BaseTool: ツールインスタンス
        """
        # コードから必要なモジュールを抽出
        imports = self._extract_imports(tool_code)
        
        # 不足しているモジュールを自動インストール
        self._install_missing_modules(imports)
        
        # 安全な名前空間を準備
        namespace = {
            'BaseTool': BaseTool,
            'BaseModel': None,
            'Field': None,
            'Type': None,
        }
        
        # 必要なインポートを追加
        imports = """
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import json
import requests
"""
        
        # コードを実行して動的にクラスを作成
        full_code = imports + "\n" + tool_code
        exec(full_code, namespace)
        
        # 生成されたツールクラスを取得
        tool_class = None
        for name, obj in namespace.items():
            if (isinstance(obj, type) and
                    issubclass(obj, BaseTool) and
                    obj != BaseTool and
                    name != 'BaseTool'):
                tool_class = obj
                break
        
        if not tool_class:
            raise ValueError("Tool class not found in generated code")
        
        # インスタンス化
        try:
            tool_instance = tool_class()
        except Exception as e:
            raise ValueError(f"Failed to instantiate tool: {str(e)}")
        
        return tool_instance
