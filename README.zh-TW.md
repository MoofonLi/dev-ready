# dev-ready

[![CI](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dev-ready)](https://pypi.org/project/dev-ready/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 本頁是給中文讀者的導覽，說明 dev-ready 是什麼、產出什麼、怎麼跑第一次。
> 完整的命令列參考與開發說明請見 [English README](README.md)。
> dev-ready 本身的介面與產生的專案內容一律為英文（[ADR-016](docs/decisions/adr-016-language-boundary.md)）。

一行指令，產生一個已為 AI 協作開發配置好的 FastAPI + React 專案：

```bash
uvx dev-ready init my-app
```

不會產生做到一半的輸出，也不會抓未經測試的「最新版」：上游範本固定在通過 CI 驗證的 commit，而且產生過程是全有全無——任何一步失敗，你的目標目錄不會被碰到。

## 你會得到什麼

一個以 [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 為基底的專案（FastAPI、React、SQLModel、PostgreSQL、Docker Compose），外加一層 AI 工具疊加內容，讓 coding agent 一開箱就能順利工作：

- **專案指示與開發護欄** — 共用內容只寫一份在標準位置；支援標準的 agent 可直接讀取，而凡是需要自己專屬目錄的 agent，只要固定參考清單裡有它，dev-ready 就會為它建立一份指向共用內容的連結。該連結只存在於本機、不進 git，clone 之後跑一次 `uvx dev-ready upgrade` 就會重建，讓它讀到同一份指示。專案的 `AGENTS.md` 也會寫明這個專案實際用了哪些技術、測試與檢查各該跑哪些指令，以及它本身就是這個專案的標準來源
- **具名的 Engineering Flow** — 每個專案都會先選定一套開發方法（兩套可選、一套標成即將推出）
- **精簡的預設內容** — 接受預設值時，只產生這套 Engineering Flow 加上專案自己的架構與需求文件骨架；其他強化項目預設都不加入。登入、寄信與錯誤回報可以不用親手改 `.env` 就設定好
- **依用途挑選的強化項目** — 可依開發、安全、品質、設計與 token 最佳化等類別，選擇安全稽核、React 分析、瀏覽器測試、前端設計參考、精簡 agent 回應與 codebase-memory 等能力
- **按需產生的 MCP 設定** — 只有選到需要專案層級 MCP 設定的強化項目時才會寫入設定檔，工具版本仍然固定
- **一開始就顧好機密** — 產生的 `.env` 裡是這個專案專屬的隨機密鑰，而且從第一次 commit 就被 git 忽略；專案也會告訴你預設管理者帳號是什麼、密碼放在哪裡
- **產生戳記 `.dev-ready.json`** — 記錄不可變的基底來源，以及目前選取的類別、開發循環、強化項目、agent 目標、版本固定值與受管理檔案清單

每個產生的專案也會有自己的 `README.md`。上游範本自身的 repo 維護檔案（`CONTRIBUTING.md`、發布說明、截圖等）會被清掉，不會有範本 repo 專屬的東西滲進你的專案。

## 環境需求

- Python 3.12 以上（uv 可以自動幫你裝）
- git（Copier 透過 git 取得固定版本的範本）
- 能連到 github.com
- 目標目錄需要能保存連結的檔案系統，除非沒有選任何 Agent Target
- 產生專案**不需要** Docker，只有跑起來才需要

## 安裝與第一次執行

用 [uv](https://docs.astral.sh/uv/) 不需要安裝：

```bash
uvx dev-ready init my-app
```

或用 pip（需 Python 3.12 以上）：

```bash
pip install dev-ready
dev-ready init my-app
```

直接執行時會進入互動模式，先問 Engineering Flow，再依序出示每一個可選類別，最後問 agent 目標；一路按 Enter 仍會得到上面描述的精簡內容。

產生過程中，stderr 會顯示「取得範本 → 疊加內容 → 驗證 → 完成」四個階段的進度；在終端機是動態指示器，被重導向時則是穩定的純文字行。

## 專案建立之後

dev-ready 不是產生完就結束。已產生的專案可以檢查與升級：

- **檢查（check）** — 唯讀、離線，比對專案現況與它的戳記，列出偏移
- **升級（upgrade）** — 只更新疊加層管理的檔案，且是交易式的：可先預覽、失敗會把寫入與刪除一起回滾、已淘汰且未修改的受管理檔案會刪除、你手動改過的檔案會保留並列入報告，上游應用程式碼與基底來源記錄不會被更動

完整用法請見 [English README](README.md) 與 [CLI 規格](docs/cli-spec.md)。

## 運作方式

版本固定值存放在套件內的清單檔（manifest）裡，產生時絕不去解析「latest」。每週有 GitHub Actions 自動開 PR 更新固定版本，而 CI 驗證每個 PR 的方式是真的產生一個專案、用 Docker Compose 建起來、再打健康檢查端點。所以你裝到的每個 dev-ready 版本，帶的都是它被測過的那個固定版本。

## 遇到問題

安裝或產生過程有問題，請到 <https://github.com/MoofonLi/dev-ready/issues> 開 issue（用中文或英文都可以）。

## 授權

MIT，見 [LICENSE](LICENSE)。產生的專案含有衍生自 fastapi/full-stack-fastapi-template（MIT）的內容，見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
