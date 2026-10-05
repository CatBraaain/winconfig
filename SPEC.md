# winconfig SPEC

TS実装のwinconfig CLIの完成状態を定める。winconfigは、Windowsの構成(レジストリ、スケジュールタスク、サービス、PowerShellスクリプト)を宣言的定義から適用(apply)・解除(revert)するCLIツールである。GUI/TUIはコマンドとして提供しない。実装言語はTypeScript、ランタイムはbun。

## 用語

- **タスク**: 定義YAMLの1定義。グループ名と名前で識別し、`apply`と`revert`の2方向の操作を持つ
- **ActionMode**: タスクへの操作指定。`apply`(適用) / `revert`(解除) / `skip`(何もしない)
- **状態コード**: タスク内の操作結果を表す固定文字列。`<Exist>` / `<NotExist>` / `<NotChange>` / `<AccessDenied>` / `<PermissionDenied>`

## コマンド

### `run`

```
winconfig run <configs...> [--reverse] [--dry-run] [--loglevel DEBUG|INFO|WARNING|ERROR|SILENT]
```

| 条件 | 操作 | 結果 |
| --- | --- | --- |
| configを指定して実行 | builtin定義とconfigをマージしてタスク一覧を構築し、Actions設定のモードで各タスクを実行 | 実行したタスクごとに`Success: <group> > <name>[<mode>]`を標準エラーへ出力し、終了コード0 |
| `--reverse`を指定 | Actions設定の`apply`を`revert`へ、`revert`を`apply`へ反転して実行 | 反転後のモードで適用される |
| Actions設定にないタスクが存在 | そのタスクを実行しない | `NoAction: <group> > <name>`を標準エラーへ出力 |
| モードが`skip` | そのタスクを実行しない | `Skipped: <group> > <name>[skip]`を標準エラーへ出力 |
| タスクのスクリプトが失敗 | 未開始のタスクを実行せず、実行中のタスクの完了を待つ | 失敗したタスク名・モード・生成スクリプト・例外メッセージを標準エラーへ出力し、終了コード1 |
| `--dry-run`を指定 | タスクを1つも実行しない | マージと検証の結果のみを出力し、終了コード0(設定不正なら終了コード1) |
| スクリプトが`<PermissionDenied>`を出力 | タスクを失敗扱いにする | エラーメッセージに管理者権限の必要性を含める |

### `script`

```
winconfig script <configs...> --mode apply|revert [--output <file>]
```

| 条件 | 操作 | 結果 |
| --- | --- | --- |
| `--mode`を指定して実行 | 全タスクのスクリプトを指定モードで生成し、タスク順に連結 | 標準出力へPowerShellスクリプトのテキストを出力する。Actions設定と`--reverse`は無視する |
| `--output`を指定 | 同じ内容を指定パスへUTF-8で書き込む | 標準出力へは出力しない |

### `schema`

```
winconfig schema [<configs...>] [--output <file>] [--strict]
```

| 条件 | 操作 | 結果 |
| --- | --- | --- |
| 実行 | builtin定義からConfigのJSON Schemaを生成 | UTF-8のJSON(2スペースインデント、非ASCIIをエスケープしない)を標準出力へ出力 |
| `--strict`を指定 | `Actions`のプロパティをbuiltinタスク名で固定 | `additionalProperties: false`となり、タスク名以外のキーが検証で失敗する |
| `--output`を指定 | 同じ内容を指定パスへ書き込む | 標準出力へは出力しない |

## 定義YAML

- 定義YAMLは`Definitions`(タスク定義)と`Actions`(タスクごとのActionMode)の2セクションを持つ
- builtin定義(タスク定義の内蔵セット)とユーザーconfigをマージする。同じキーはユーザーconfigで上書きする
- タスク定義の種別は4つ: レジストリ(`registries`)、スケジュールタスク(`scheduled_tasks`)、サービス(`services`)、スクリプト(`script`)
- レジストリ定義はパス(キー)とエントリ(値)を持ち、`old_existence`/`new_existence`と`old_value`/`new_value`でapply・revert両方向の目標状態を宣言する
- サービス・スケジュールタスク定義は、起動状態や登録内容の目標状態をapply・revert両方向で宣言する
- スクリプト定義は`apply`と`revert`のPowerShellスクリプト本文を持つ
- `schema --strict`の出力をJSON Schemaとして設定ファイルを検証すると、存在しないタスク名・不正なモード値が補完・検証で弾かれる

## スクリプト生成

- タスクのスクリプトは、タスクが持つ全定義(registriesは各エントリに展開、次いでscheduled_tasks、services、script)の生成結果を上から順に連結した1つのPowerShellスクリプトである
- モードと宣言された目標状態から、`apply`は`new_*`側、`revert`は`old_*`側の操作を生成する
- 生成スクリプトはPython実装(`src/winconfig/engine/task.py`の`generate_script`と各定義の`generate_set_script`)の出力と1文字も同一である
- 生成例(レジストリエントリ、`HKCU\Software\Example`の`Enabled`を`DWord`の`1`にapply):

```powershell
try {
    Set-ItemProperty -Path "Registry::HKCU\Software\Example" -Name "Enabled" -Type "DWord" -Value "1" -Force -ErrorAction Stop | Out-Null
}
catch [System.Management.Automation.ItemNotFoundException] {
    "<NotExist>"
}
catch [System.Management.Automation.PSArgumentException] {
    "<NotExist>"
}
catch [System.UnauthorizedAccessException] {
    "<AccessDenied>"
}
catch [System.Security.SecurityException] {
    "<PermissionDenied>"
}
```

## 実行モデル

- タスクの実行はPowerShell子プロセスのプールで行う。プールサイズの既定は4(上限はCPUコア数)
- プールのプロセスは起動時にウォームアップし、タスク実行時のプロセス起動は発生しない
- タスクは相互に独立として同時に実行する。タスク間の実行順序の依存は定義・実行ともに表現しない
- タスク1個は「そのタスクの連結スクリプト1本」であり、完了はスクリプト末尾の終了マーカーの出力で判定する
- タスク内のスクリプトは冪等の単位として扱い、ワーカー内では投げ込まれた順に実行する

## パフォーマンス特性

- I/O待ち150msのタスク20個をプール4で実行した場合の総時間は、単一常駐プロセス逐次実行の0.5倍以下である(2026-10-05実測: 逐次3.29sに対しプール4で0.83s)
- 同条件で、タスクごとにPowerShellプロセスを起動する方式と比較して10倍以上速い(同実測: 24.35s)
- プールの起動+ウォームアップは1回あたり2秒以内(同実測: 1.22s/4プロセス)

## 配布

- `bun build --compile`による単一実行ファイル(Windows x64)として配布する
- バージョン更新はwinget(komac)経由で行う
- 管理者権限は実行環境(管理者シェル)で確保する。自動昇格は行わない
