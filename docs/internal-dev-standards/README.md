# 內部系統開發規範 Internal Development Standards

## 概覽 Overview

本文檔集合定義了公司內部系統開發的統一規範，涵蓋前端、後端、DevOps、資料庫管理等各個領域，旨在確保程式碼品質、系統穩定性和團隊協作效率。

This documentation set defines unified development standards for internal systems, covering frontend, backend, DevOps, database management, and other areas to ensure code quality, system stability, and team collaboration efficiency.

## 技術棧 Technology Stack

### 前端 Frontend
- **框架**: Vite + Vue 3 + Pinia + TypeScript
- **HTTP客戶端**: Axios
- **UI框架**: Vuetify UI
- **程式碼品質**: Prettier + ESLint
- **版本**: 使用最新穩定版本

### 後端 Backend
- **.NET**: .NET 8 Web API + Entity Framework Core
- **Python**: Python 3.13 + FastAPI + SQLAlchemy
- **套件管理**: uv (Python)
- **程式碼品質**: Black + Flake8/Pylint
- **版本**: 使用最新穩定版本

### 資料庫 Database
- **主要資料庫**: PostgreSQL 16

### 基礎設施 Infrastructure
- **反向代理**: Nginx
- **API Gateway**: Kong (JWT驗證)
- **容器化**: Docker + Docker Compose
- **消息隊列**: Kafka (按需使用)

### 版本控制與部署 Version Control & Deployment
- **版本控制**: Git + GitLab
- **CI/CD**: GitLab CI
- **專案管理**: Monorepo

## 環境配置 Environment Configuration

### 環境類型
- `development` - 開發環境
- `testing` - 測試環境
- `production` - 生產環境

### 認證與授權
- **SSO**: 統一使用 JWT
- **驗證流程**: 後端透過 Kong 驗證，前端從 cookie 取出 JWT
- **服務整合**: Auth Service + User Service (RBAC)

## 文檔結構 Documentation Structure

### 按角色分類 By Role

1. **[前端工程師規範](./frontend-standards.md)**
   - Vue 3 + TypeScript 開發規範
   - 元件設計原則
   - 狀態管理規範
   - UI/UX 標準

2. **[Python FastAPI 後端規範](./python-fastapi-standards.md)**
   - Python 3.13 + FastAPI 開發規範
   - Clean Architecture 設計
   - 領域驅動設計 (DDD)
   - 非同步程式設計

3. **[C# .NET 後端規範](./csharp-dotnet-standards.md)**
   - .NET 8 + ASP.NET Core 開發規範
   - Clean Architecture 設計
   - Entity Framework Core Code First
   - 依賴注入與測試

4. **[DevOps 規範](./devops-standards.md)**
   - CI/CD 流程
   - 容器化標準
   - 部署策略
   - 監控與日誌

5. **[DBA 規範](./dba-standards.md)**
   - 資料庫設計規範
   - 效能優化標準
   - 備份與恢復
   - 安全性規範

### 按功能分類 By Function

6. **[API 設計規範](./api-standards.md)**
   - RESTful 設計原則
   - 請求/回應格式
   - 版本控管
   - 錯誤處理

7. **[版本控制與 CI/CD 規範](./version-control-cicd.md)**
   - Git 工作流程
   - Commit 規範
   - Branch 策略
   - 自動化測試

### 微服務與事件驅動架構 Microservices & Event-Driven Architecture

8. **[微服務架構規範](./microservices-architecture-standards.md)**
   - 微服務設計原則與拆分策略
   - 領域驅動設計 (DDD) 實踐
   - API Gateway 設計 (Kong)
   - 服務間通訊與斷路器模式
   - 分散式事務管理 (Saga 模式)
   - 服務監控與健康檢查

9. **[事件驅動架構規範](./event-driven-architecture-standards.md)**
   - Kafka 配置與管理
   - 事件建模與設計
   - 事件發布與訂閱模式
   - 事件溯源 (Event Sourcing)
   - CQRS 模式實作
   - 事件處理保證與錯誤處理

10. **[容器化與編排規範](./containerization-orchestration-standards.md)**
    - Docker 微服務容器化策略
    - Docker Compose 編排配置
    - 環境變數與設定管理
    - 網路隔離與安全配置
    - 監控與日誌收集
    - CI/CD 容器化整合

## 程式碼品質標準 Code Quality Standards

### 前端
- **格式化**: Prettier (自動格式化)
- **Linting**: ESLint (程式碼檢查)
- **要求**: 必須通過 CI 檢查才能合併

### Python 後端
- **格式化**: Black (自動格式化)
- **Linting**: Flake8/Pylint (程式碼檢查)
- **要求**: 自動格式化並通過 lint 檢查才能合併

### .NET 後端
- **格式化**: 內建 .NET 格式化工具
- **分析**: .NET Code Analysis
- **要求**: 遵循 Microsoft 程式碼規範

## 核心原則 Core Principles

1. **非同步優先**: 系統設計以 `async` 為主
2. **前後端分離**: 清楚的職責劃分
3. **容器化部署**: 統一的部署方式
4. **自動化測試**: 完整的測試覆蓋
5. **文檔驅動**: 完善的文檔記錄
6. **安全第一**: 內建安全考量

## 快速開始 Quick Start

1. 閱讀對應角色的開發規範
2. 設置開發環境
3. 遵循程式碼品質標準
4. 執行測試並確保通過
5. 提交代碼並通過 CI 檢查

## 更新記錄 Update History

- **v1.0.0** (2025-01-XX): 初始版本發布
- 後續更新將記錄在此處

## 聯絡資訊 Contact Information

如有問題或建議，請聯絡：
- 技術負責人
- 開發團隊

---

*最後更新: 2025-01-XX*
