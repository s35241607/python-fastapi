# 版本控制與 CI/CD 規範 Version Control & CI/CD Standards

## 目錄 Table of Contents

1. [Git 工作流程](#git-工作流程)
2. [分支策略](#分支策略)
3. [Commit 規範](#commit-規範)
4. [程式碼審查](#程式碼審查)
5. [CI/CD 流程](#cicd-流程)
6. [部署策略](#部署策略)

## Git 工作流程

### 分支模式
我們採用 **GitLab Flow** 結合 **Feature Branch** 的工作模式：

```
main (生產環境)
  ↑
develop (開發環境)
  ↑
feature/ticket-123-description (功能分支)
```

### 分支類型
```bash
# 主要分支
main                    # 穩定的生產版本
develop                 # 最新的開發版本

# 功能分支
feature/ticket-123-user-authentication
feature/add-payment-gateway

# 發布分支
release/v1.2.0

# 修復分支
hotfix/fix-critical-security-issue
```

## 分支策略

### 功能開發流程

#### 1. 建立功能分支
```bash
git checkout develop
git pull origin develop
git checkout -b feature/ticket-123-user-authentication
```

#### 2. 開發與提交
```bash
git add .
git commit -m "feat(auth): add JWT token validation

- Implement JWT token validation middleware
- Add token expiration check
- Update user authentication flow

Closes PROJ-123"
```

#### 3. 合併請求
```bash
git push origin feature/ticket-123-user-authentication
# 在 GitLab 建立 Merge Request
```

### 發布流程
```bash
# 建立發布分支
git checkout develop
git checkout -b release/v1.2.0

# 合併到 main
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"

# 合併回 develop
git checkout develop
git merge --no-ff release/v1.2.0
```

## Commit 規範

### Conventional Commits 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit 類型
```bash
feat(auth): add OAuth2 integration          # 功能新增
fix(api): resolve user profile update       # 修復問題
docs(readme): update installation guide     # 文檔更新
style(frontend): fix code formatting        # 樣式調整
refactor(service): restructure user service # 重構
perf(database): optimize user query         # 效能改善
test(user): add integration tests           # 測試相關
build(deps): update dependency versions     # 建構工具
ci(gitlab): add automated deployment        # CI/CD 相關
chore(docker): update Dockerfile            # 其他雜項
```

### 好的 Commit 訊息範例
```bash
feat(ticket): implement advanced search functionality

- Add full-text search capability
- Support multiple filter criteria
- Implement pagination for search results
- Add search result highlighting

Closes PROJ-456
Performance impact: Search queries now 40% faster
```

## 程式碼審查

### Merge Request 規範

#### MR 標題格式
```
<type>(<scope>): <description>

範例:
feat(user): implement user profile management
fix(api): resolve authentication token expiration issue
```

#### MR 描述範本
```markdown
## 變更概述
簡要描述此 MR 的主要變更內容。

## 變更類型
- [ ] 新功能 (feat)
- [ ] 修復問題 (fix)
- [ ] 重構 (refactor)
- [ ] 文檔更新 (docs)

## 測試內容
- [ ] 單元測試已通過
- [ ] 整合測試已通過
- [ ] 手動測試已完成

## 檢查清單
- [ ] 程式碼已通過 linting 檢查
- [ ] 所有測試都已通過
- [ ] 文檔已更新

## 相關 Issue
Closes #123
```

### 審查標準
```markdown
### 程式碼品質檢查
- [ ] 功能實現正確
- [ ] 遵循命名規範
- [ ] 錯誤處理完善
- [ ] 無安全風險
- [ ] 測試覆蓋充分
```

## CI/CD 流程

### GitLab CI 配置

#### 基本 Pipeline 結構
```yaml
stages:
  - validate
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "22"
  PYTHON_VERSION: "3.13"

# 前端 Lint 檢查
frontend:lint:
  stage: validate
  image: node:${NODE_VERSION}-alpine
  script:
    - cd frontend
    - npm ci
    - npm run lint:check
    - npm run format:check
    - npm run type-check
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

# 後端 Lint 檢查
backend:lint:
  stage: validate
  image: python:${PYTHON_VERSION}-slim
  script:
    - cd backend
    - pip install uv
    - uv sync
    - uv run black --check .
    - uv run flake8 .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

# 前端測試
frontend:test:
  stage: test
  image: node:${NODE_VERSION}-alpine
  script:
    - cd frontend
    - npm ci
    - npm run test:unit -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: frontend/coverage/cobertura-coverage.xml

# 後端測試
backend:test:
  stage: test
  image: python:${PYTHON_VERSION}-slim
  services:
    - postgres:16-alpine
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
    DATABASE_URL: postgresql+asyncpg://test_user:test_password@postgres:5432/test_db
  script:
    - cd backend
    - pip install uv
    - uv sync
    - uv run pytest --cov=app --cov-report=xml tests/
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/coverage.xml

# 建構映像
build:images:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker build -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA ./backend
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

# 部署到測試環境
deploy:staging:
  stage: deploy
  image: alpine:latest
  environment:
    name: staging
    url: https://staging.yourdomain.com
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
  script:
    - ssh $STAGING_USER@$STAGING_SERVER "
        cd /opt/app &&
        export IMAGE_TAG=$CI_COMMIT_SHA &&
        docker-compose -f docker-compose.staging.yml pull &&
        docker-compose -f docker-compose.staging.yml up -d"
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

# 部署到生產環境
deploy:production:
  stage: deploy
  image: alpine:latest
  environment:
    name: production
    url: https://yourdomain.com
  script:
    - ssh $PRODUCTION_USER@$PRODUCTION_SERVER "
        cd /opt/app &&
        export IMAGE_TAG=$CI_COMMIT_SHA &&
        docker-compose -f docker-compose.prod.yml pull &&
        docker-compose -f docker-compose.prod.yml up -d"
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### 品質門檻
```yaml
# 程式碼品質要求
quality_gates:
  coverage:
    frontend: 80%
    backend: 85%

  lint:
    frontend: 0 errors
    backend: 0 errors

  security:
    vulnerabilities: 0 high/critical

  performance:
    build_time: < 10 minutes
    test_time: < 5 minutes
```

## 部署策略

### 環境配置
```yaml
environments:
  development:
    branch: "develop"
    auto_deploy: true

  staging:
    branch: "develop"
    auto_deploy: true

  production:
    branch: "main"
    auto_deploy: false  # 需要手動觸發
```

### 藍綠部署腳本
```bash
#!/bin/bash
# scripts/blue_green_deploy.sh

NEW_VERSION=${1:-latest}

# 檢查當前活躍環境
CURRENT_ENV=$(curl -s http://load-balancer/health | jq -r '.environment')
TARGET_ENV=$([ "$CURRENT_ENV" == "blue" ] && echo "green" || echo "blue")

echo "📍 Current: $CURRENT_ENV → Target: $TARGET_ENV"

# 部署到目標環境
docker-compose -f docker-compose.$TARGET_ENV.yml pull
docker-compose -f docker-compose.$TARGET_ENV.yml up -d

# 健康檢查
for i in {1..30}; do
    if curl -f http://$TARGET_ENV-app:8000/health; then
        echo "✅ Health check passed"
        break
    fi
    sleep 10
done

# 切換流量
curl -X POST http://load-balancer/switch-environment \
    -d "{\"target\": \"$TARGET_ENV\"}"

echo "✅ Deployment successful!"
```

### 版本發布

#### 語義化版本控制
```
MAJOR.MINOR.PATCH

範例:
1.0.0    # 穩定版本
1.1.0    # 新增功能
1.1.1    # 修復問題
2.0.0    # 重大變更
```

#### 自動版本標記
```bash
#!/bin/bash
# scripts/auto_version.sh

CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
COMMITS=$(git log $CURRENT_VERSION..HEAD --oneline)

# 決定版本類型
if echo "$COMMITS" | grep -q "BREAKING CHANGE\|feat!:"; then
    VERSION_TYPE="major"
elif echo "$COMMITS" | grep -q "feat:"; then
    VERSION_TYPE="minor"
else
    VERSION_TYPE="patch"
fi

# 計算新版本號
NEW_VERSION=$(npx semver $CURRENT_VERSION -i $VERSION_TYPE)

# 更新版本並建立標籤
echo "$NEW_VERSION" > VERSION
git add VERSION
git commit -m "bump: version $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
git push origin main --tags

echo "✅ Version $NEW_VERSION released!"
```

### Git Hooks

#### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit

# 阻止直接提交到 main 或 develop
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "main" ] || [ "$branch" = "develop" ]; then
    echo "❌ Direct commits to $branch are not allowed"
    exit 1
fi

# 執行程式碼品質檢查
npm run lint:check && npm run test:unit
```

#### Commit-msg Hook
```bash
#!/bin/sh
# .git/hooks/commit-msg

# 檢查 commit 訊息格式
commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format"
    echo "💡 Use: type(scope): description"
    exit 1
fi
```

### 最佳實踐檢查清單

#### 開發流程
- [ ] 從 develop 建立功能分支
- [ ] 使用有意義的分支名稱
- [ ] 頻繁提交小的變更
- [ ] 撰寫清楚的 commit 訊息
- [ ] 定期與 develop 同步

#### 程式碼品質
- [ ] 程式碼通過 lint 檢查
- [ ] 單元測試覆蓋率達標
- [ ] 整合測試通過
- [ ] 文檔更新完成

#### 發布準備
- [ ] 功能測試完成
- [ ] 效能測試通過
- [ ] 安全掃描無問題
- [ ] 版本號更新正確

---

*最後更新: 2025-01-XX*
