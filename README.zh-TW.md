# dev-ready

[![CI](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dev-ready)](https://pypi.org/project/dev-ready/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 本頁是給中文讀者的導覽，說明 dev-ready 是什麼、產出什麼、怎麼跑第一次。
> 完整的旗標、退出碼與開發說明請見 [English README](README.md)。
> dev-ready 本身的介面與產生的專案內容一律為英文（[ADR-016](docs/decisions/adr-016-language-boundary.md)）。

一行指令，產生一個已為 AI 協作開發配置好的 FastAPI + React 專案：

```bash
uvx dev-ready init my-app
```

不會產生做到一半的輸出，也不會抓未經測試的「最新版」：上游範本固定在通過 CI 驗證的 commit，而且產生過程是全有全無——任何一步失敗，你的目標目錄不會被碰到。

## 你會得到什麼

一個以 [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 為基底的專案（FastAPI、React、SQLModel、PostgreSQL、Docker Compose），外加一層 AI 工具疊加內容，讓 coding agent 一開箱就能順利工作：

- **專案指示與開發護欄** — 共用內容只寫一份在標準位置；支援標準的 agent 可直接讀取，另有需要的 agent 則透過指向共用內容的普通檔案使用同一份指示
- **技能目錄（skills）** — 技能只在標準位置保存一份並可逐項挑選。`spec-loop` 這組會帶入規劃、可留存的規格、tracer-bullet 工單、TDD、審查、除錯與架構改善的完整流程
- **MCP 伺服器設定** — 包含可選的 codebase-memory 伺服器（版本已固定）
- **設計文件範本** — 架構與需求文件的起始骨架
- **可設定的交接協議（Handoff Protocol）** — 七個穩定角色、交接順序、升級路徑、審查關卡與提交權限，全部是可編輯的設定資料，執行時以該設定為準
- **產生戳記 `.dev-ready.json`** — 記錄基底來源、選取的元件與版本固定值，以及受管理檔案的清單

每個產生的專案也會有自己的 `README.md`。上游範本自身的 repo 維護檔案（`CONTRIBUTING.md`、發布說明、部署 workflow、截圖等）會被清掉，不會有範本 repo 專屬的東西滲進你的專案。

## 環境需求

- Python 3.12 以上（uv 可以自動幫你裝）
- git（Copier 透過 git 取得固定版本的範本）
- 能連到 github.com
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

直接執行 `uvx dev-ready init` 會進入互動模式，逐項詢問；命令列上已經給過的就不再問。想要完全不互動、全用預設值，加上 `--yes`。

產生過程中，stderr 會顯示「取得範本 → 疊加內容 → 驗證 → 完成」四個階段的進度；在終端機是動態指示器，被重導向時則是穩定的純文字行。

### 讓你的 agent 直接呼叫

這個 repo 也提供一個跨 agent 的技能，可直接安裝：

```bash
npx skills add MoofonLi/dev-ready --skill dev-ready
```

裝好之後直接跟你的 agent 說：「用 dev-ready 建一個叫 my-app 的 FastAPI 專案。」它會檢查目標位置、決定要選哪些元件、以單一非互動指令產生專案，並驗證產出的戳記。

## 專案建立之後

dev-ready 不是產生完就結束。已產生的專案可以檢查與升級：

- **檢查（check）** — 唯讀、離線，比對專案現況與它的戳記，列出偏移
- **升級（upgrade）** — 只更新疊加層管理的檔案，且是交易式的：可先預覽、失敗會整批回滾、你手動改過的檔案一律保留不覆蓋，上游應用程式碼與基底來源記錄不會被更動

指令與旗標的完整說明請見 [English README](README.md) 與 [CLI 規格](docs/cli-spec.md)。

## 運作方式

版本固定值存放在套件內的清單檔（manifest）裡，產生時絕不去解析「latest」。每週有 GitHub Actions 自動開 PR 更新固定版本，而 CI 驗證每個 PR 的方式是真的產生一個專案、用 Docker Compose 建起來、再打健康檢查端點。所以你裝到的每個 dev-ready 版本，帶的都是它被測過的那個固定版本。

## 遇到問題

安裝或產生過程有問題，請到 <https://github.com/MoofonLi/dev-ready/issues> 開 issue（用中文或英文都可以）。

## 授權

MIT，見 [LICENSE](LICENSE)。產生的專案含有衍生自 fastapi/full-stack-fastapi-template（MIT）的內容，見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
