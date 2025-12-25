---
name: generate-acceptance-test
description: 從規格目錄的 acceptance.yaml 生成/維護 BDD/ezSpec 測試。支援 Gherkin 語法，確保「規格即測試」，並與 Frame Concerns 建立可追溯連結。
---

# Generate Acceptance Test Skill

## 觸發時機

- analyze-frame 產生規格目錄後
- acceptance/acceptance.yaml 更新時
- 需求異動需同步更新驗收測試時
- 代碼生成前，希望先鎖定可執行的驗收測試

## 核心任務

1. 解析 acceptance/acceptance.yaml 的測試規格
2. 生成 ezSpec (Gherkin) 格式的 .feature 檔案
3. 維護規格與測試的一致性
4. 建立與 Frame Concerns 的可追溯連結

---

## 規格目錄結構

```
docs/specs/{feature-name}/
├── frame.yaml
├── acceptance/
│   ├── acceptance.yaml        # 測試規格 (輸入)
│   └── generated/
│       └── {feature}.feature  # ezSpec 輸出
└── ...
```

---

## acceptance/acceptance.yaml 格式

```yaml
# docs/specs/{feature-name}/acceptance/acceptance.yaml
acceptance:
  feature: "{Feature Name}"
  description: |
    {Feature 描述，可對應 User Story}
  
  # 與 Frame Concerns 的連結
  validates_concerns:
    - FC1
    - FC2
  
  # ---------------------------------------------------------------------------
  # 測試場景
  # ---------------------------------------------------------------------------
  
  scenarios:
    - id: AT1
      name: "Successfully create workflow"
      type: happy-path  # | error-case | edge-case | boundary
      priority: critical  # | high | medium | low
      tags:
        - "@smoke"
        - "@api"
      
      # BDD 格式
      given:
        - condition: "User is authenticated"
          setup: "AuthFixture.authenticatedUser()"
        - condition: "User is a board member"
          setup: "BoardFixture.memberOf(boardId)"
        - condition: "Board exists with id 'board-123'"
          setup: "BoardFixture.exists(boardId)"
      
      when:
        - action: "User creates workflow with name 'Sprint 1'"
          trigger: "CreateWorkflowUseCase.execute(input)"
      
      then:
        - expectation: "Workflow is created with generated ID"
          assertion: "result.workflowId should not be null"
        - expectation: "WorkflowCreated event is published"
          assertion: "eventPublisher.published contains WorkflowCreatedEvent"
      
      # 連結到契約
      validates_contracts:
        - machine/use-case.yaml#contracts.post_conditions.POST1
      
      # 連結到 invariants
      validates_invariants:
        - controlled-domain/aggregate.yaml#invariants.shared.INV1
    
    # -------------------------------------------------------------------------
    # Error Cases
    # -------------------------------------------------------------------------
    
    - id: AT2
      name: "Fail when user is not authorized"
      type: error-case
      priority: critical
      tags:
        - "@security"
      
      given:
        - condition: "User is authenticated"
        - condition: "User is NOT a board member"
      
      when:
        - action: "User attempts to create workflow"
      
      then:
        - expectation: "UnauthorizedError is thrown"
          error_type: "UnauthorizedError"
        - expectation: "No workflow is created"
          assertion: "workflowRepository.count() == 0"
      
      validates_contracts:
        - cross-context/authorization.yaml#required_capability
    
    # -------------------------------------------------------------------------
    # Edge Cases
    # -------------------------------------------------------------------------
    
    - id: AT3
      name: "Handle concurrent workflow creation"
      type: edge-case
      priority: high
      tags:
        - "@concurrency"
      
      given:
        - condition: "Two users attempt to create workflow simultaneously"
      
      when:
        - action: "Both submit create workflow request at the same time"
      
      then:
        - expectation: "Only one workflow is created"
        - expectation: "The other request receives ConflictError"
      
      validates_concerns:
        - FC2  # Concurrency concern
  
  # ---------------------------------------------------------------------------
  # 測試資料
  # ---------------------------------------------------------------------------
  
  test_data:
    - name: "validWorkflowInput"
      type: "CreateWorkflowInput"
      value:
        boardId: "board-123"
        name: "Sprint 1"
        operatorId: "user-456"
    
    - name: "invalidWorkflowInput"
      type: "CreateWorkflowInput"
      value:
        boardId: ""
        name: ""
        operatorId: "user-456"
```

---

## 生成的 ezSpec (Gherkin) 格式

```gherkin
# docs/specs/{feature-name}/acceptance/generated/{feature}.feature
# Auto-generated from acceptance.yaml - DO NOT EDIT DIRECTLY
# Last generated: {ISO-8601}
# Validates: FC1, FC2

@feature-{feature-name}
Feature: {Feature Name}
  {Feature 描述}

  Background:
    Given the system is initialized
    And test fixtures are prepared

  # ===== Happy Path =====
  
  @smoke @api @AT1
  Scenario: Successfully create workflow
    # Validates: POST1, INV1
    Given User is authenticated
    And User is a board member
    And Board exists with id "board-123"
    When User creates workflow with name "Sprint 1"
    Then Workflow is created with generated ID
    And WorkflowCreated event is published

  # ===== Error Cases =====
  
  @security @AT2
  Scenario: Fail when user is not authorized
    # Validates: XC1 (Authorization)
    Given User is authenticated
    But User is NOT a board member
    When User attempts to create workflow
    Then UnauthorizedError is thrown
    And No workflow is created

  # ===== Edge Cases =====
  
  @concurrency @AT3
  Scenario: Handle concurrent workflow creation
    # Validates: FC2 (Concurrency)
    Given Two users attempt to create workflow simultaneously
    When Both submit create workflow request at the same time
    Then Only one workflow is created
    And The other request receives ConflictError
```

---

## TypeScript 測試骨架生成

```typescript
// tests/acceptance/CreateWorkflow.spec.ts
// Auto-generated from acceptance.yaml

import { describe, it, beforeEach, expect } from 'vitest';
import { CreateWorkflowUseCase } from '@/application/use-cases/CreateWorkflowUseCase';
import { InMemoryWorkflowRepository } from '@/infrastructure/repositories/InMemoryWorkflowRepository';
import { MockEventPublisher } from '@/tests/mocks/MockEventPublisher';
import { AuthFixture, BoardFixture } from '@/tests/fixtures';

describe('Feature: Create Workflow', () => {
  let useCase: CreateWorkflowUseCase;
  let workflowRepository: InMemoryWorkflowRepository;
  let eventPublisher: MockEventPublisher;

  beforeEach(() => {
    workflowRepository = new InMemoryWorkflowRepository();
    eventPublisher = new MockEventPublisher();
    useCase = new CreateWorkflowUseCase(
      /* dependencies injected */
    );
  });

  // ===== AT1: Successfully create workflow =====
  // Validates: POST1, INV1
  // Tags: @smoke @api
  describe('Scenario: Successfully create workflow', () => {
    it('should create workflow with generated ID', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      const board = await BoardFixture.exists('board-123');
      await BoardFixture.memberOf(user.id, board.id);

      // When
      const input = {
        boardId: 'board-123',
        name: 'Sprint 1',
        operatorId: user.id,
      };
      const result = await useCase.execute(input);

      // Then
      expect(result.workflowId).toBeDefined();
      expect(result.workflowId).not.toBeNull();
    });

    it('should publish WorkflowCreated event', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      await BoardFixture.memberOf(user.id, 'board-123');

      // When
      await useCase.execute({
        boardId: 'board-123',
        name: 'Sprint 1',
        operatorId: user.id,
      });

      // Then
      expect(eventPublisher.published).toContainEqual(
        expect.objectContaining({ type: 'WorkflowCreatedEvent' })
      );
    });
  });

  // ===== AT2: Fail when user is not authorized =====
  // Validates: XC1 (Authorization)
  // Tags: @security
  describe('Scenario: Fail when user is not authorized', () => {
    it('should throw UnauthorizedError', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      // User is NOT a board member

      // When & Then
      await expect(
        useCase.execute({
          boardId: 'board-123',
          name: 'Sprint 1',
          operatorId: user.id,
        })
      ).rejects.toThrow(UnauthorizedError);
    });

    it('should not create any workflow', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      const initialCount = await workflowRepository.count();

      // When
      try {
        await useCase.execute({
          boardId: 'board-123',
          name: 'Sprint 1',
          operatorId: user.id,
        });
      } catch (e) {
        // Expected
      }

      // Then
      expect(await workflowRepository.count()).toBe(initialCount);
    });
  });

  // ===== AT3: Handle concurrent workflow creation =====
  // Validates: FC2 (Concurrency)
  // Tags: @concurrency
  describe('Scenario: Handle concurrent workflow creation', () => {
    it('should only create one workflow', async () => {
      // Given
      const user1 = AuthFixture.authenticatedUser('user-1');
      const user2 = AuthFixture.authenticatedUser('user-2');
      await BoardFixture.memberOf(user1.id, 'board-123');
      await BoardFixture.memberOf(user2.id, 'board-123');

      // When: Concurrent execution
      const [result1, result2] = await Promise.allSettled([
        useCase.execute({ boardId: 'board-123', name: 'Sprint 1', operatorId: user1.id }),
        useCase.execute({ boardId: 'board-123', name: 'Sprint 1', operatorId: user2.id }),
      ]);

      // Then
      const fulfilled = [result1, result2].filter(r => r.status === 'fulfilled');
      const rejected = [result1, result2].filter(r => r.status === 'rejected');
      
      expect(fulfilled.length).toBe(1);
      expect(rejected.length).toBe(1);
      expect(rejected[0].reason).toBeInstanceOf(ConflictError);
    });
  });
});
```

---

## Go 測試骨架生成

```go
// tests/acceptance/create_workflow_test.go
// Auto-generated from acceptance.yaml

package acceptance

import (
    "context"
    "testing"
    "sync"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    
    "myapp/application/usecase"
    "myapp/tests/fixtures"
    "myapp/tests/mocks"
)

func TestCreateWorkflow(t *testing.T) {
    // ===== AT1: Successfully create workflow =====
    t.Run("Scenario: Successfully create workflow", func(t *testing.T) {
        t.Run("should create workflow with generated ID", func(t *testing.T) {
            // Given
            user := fixtures.AuthenticatedUser(t)
            board := fixtures.BoardExists(t, "board-123")
            fixtures.MemberOf(t, user.ID, board.ID)
            
            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub)

            // When
            input := usecase.CreateWorkflowInput{
                BoardID:    "board-123",
                Name:       "Sprint 1",
                OperatorID: user.ID,
            }
            result, err := uc.Execute(context.Background(), input)

            // Then
            require.NoError(t, err)
            assert.NotEmpty(t, result.WorkflowID)
        })

        t.Run("should publish WorkflowCreated event", func(t *testing.T) {
            // Given
            user := fixtures.AuthenticatedUser(t)
            fixtures.MemberOf(t, user.ID, "board-123")
            
            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub)

            // When
            _, err := uc.Execute(context.Background(), usecase.CreateWorkflowInput{
                BoardID:    "board-123",
                Name:       "Sprint 1",
                OperatorID: user.ID,
            })

            // Then
            require.NoError(t, err)
            assert.Contains(t, eventPub.Published(), "WorkflowCreatedEvent")
        })
    })

    // ===== AT2: Fail when user is not authorized =====
    t.Run("Scenario: Fail when user is not authorized", func(t *testing.T) {
        t.Run("should return UnauthorizedError", func(t *testing.T) {
            // Given
            user := fixtures.AuthenticatedUser(t)
            // User is NOT a board member

            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            authSvc := mocks.NewDenyAllAuthorizationService()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub, authSvc)

            // When
            _, err := uc.Execute(context.Background(), usecase.CreateWorkflowInput{
                BoardID:    "board-123",
                Name:       "Sprint 1",
                OperatorID: user.ID,
            })

            // Then
            assert.ErrorIs(t, err, domain.ErrUnauthorized)
        })
    })

    // ===== AT3: Handle concurrent workflow creation =====
    t.Run("Scenario: Handle concurrent workflow creation", func(t *testing.T) {
        t.Run("should only create one workflow", func(t *testing.T) {
            // Given
            user1 := fixtures.AuthenticatedUser(t)
            user2 := fixtures.AuthenticatedUser(t)
            fixtures.MemberOf(t, user1.ID, "board-123")
            fixtures.MemberOf(t, user2.ID, "board-123")

            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub)

            // When: Concurrent execution
            var wg sync.WaitGroup
            results := make(chan error, 2)

            for _, userID := range []string{user1.ID, user2.ID} {
                wg.Add(1)
                go func(uid string) {
                    defer wg.Done()
                    _, err := uc.Execute(context.Background(), usecase.CreateWorkflowInput{
                        BoardID:    "board-123",
                        Name:       "Sprint 1",
                        OperatorID: uid,
                    })
                    results <- err
                }(userID)
            }
            wg.Wait()
            close(results)

            // Then
            var successCount, conflictCount int
            for err := range results {
                if err == nil {
                    successCount++
                } else if errors.Is(err, domain.ErrConflict) {
                    conflictCount++
                }
            }
            
            assert.Equal(t, 1, successCount)
            assert.Equal(t, 1, conflictCount)
        })
    })
}
```

---

## 同步檢查機制

當規格更新時，Skill 會：

1. **偵測變更**：比對 acceptance.yaml 的變更
2. **標記過時測試**：在 .feature 檔案中標記需更新的場景
3. **生成差異報告**：列出需要同步的項目

```yaml
# 同步狀態報告
sync_report:
  generated_at: "2024-12-25T10:00:00Z"
  
  in_sync:
    - AT1
    - AT2
  
  out_of_sync:
    - id: AT3
      reason: "acceptance.yaml updated, feature file not regenerated"
      diff: "then clause changed"
  
  missing:
    - id: AT4
      reason: "New scenario added to acceptance.yaml"
```

---

## 品質檢查清單

- [ ] 每個 scenario 是否都有可執行的 Given/When/Then？
- [ ] 是否涵蓋 happy-path、error-case、edge-case？
- [ ] 是否與 Frame Concerns 建立 validates_concerns 連結？
- [ ] 是否與 contracts 建立 validates_contracts 連結？
- [ ] 測試名稱、檔名是否對應 feature-name？
- [ ] 併發場景是否有測試 (若 FC 包含 Concurrency)？

---

## 與其他 Skills 的協作

```
analyze-frame
    │
    └── 生成 acceptance/acceptance.yaml
            │
            └── generate-acceptance-test (本 Skill)
                    │
                    ├── 生成 .feature (ezSpec)
                    ├── 生成 TypeScript/Go 測試骨架
                    │
                    ├── 連結 → enforce-contract (驗證 contracts)
                    └── 連結 → cross-context (驗證 ACL)
```
