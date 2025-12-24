---
name: reactor-sub-agent
description: 專責處理 RIF 類型的需求，根據 analyze-frame 的 YAML 規格設計/審查事件反應、整合與非同步流程。支援 Java、TypeScript、Go 多語言。確保冪等性、可恢復性與重試機制。
---

# Reactor Sub-agent Skill

## 觸發時機
- analyze-frame 判定 frame_type=RIF 時
- 需要新增/審查事件處理器、訊息消費者、整合流程時
- 設計重試、死信、冪等性與監控機制時
- saga-orchestrator 分派事件處理任務時

## 核心任務
1. 解析 YAML 規格中的事件來源、觸發條件與期望反應
2. 設計/審查事件處理流程、整合介面、錯誤處理與補償策略
3. 確保處理具備冪等性、可觀測性與恢復機制

## Claude Code Sub-agent 整合

本 Skill 可作為 `runSubagent` 的任務目標：

```
saga-orchestrator → runSubagent → reactor-sub-agent
                                    ├── 讀取 coding-standards
                                    ├── 設計冪等策略
                                    ├── 設計重試/死信機制
                                    └── 輸出 Event Handler 代碼
```

### 被分派時的輸入格式

```yaml
task:
  type: "reactor"
  spec_file: "docs/specs/order-created-handler.yaml"
  language: "typescript"  # java | typescript | go
  trigger_event: "OrderCreated"
  output_path: "src/application/handlers/"
```

## 工作流程
1. **解析規格**：讀取 metadata.frame_type=RIF；提取 problem_statement、acceptance_criteria、technical_constraints。
2. **處理器設計**：
   - 定義 Event Handler / Consumer 介面與輸入模型
   - 明確輸入驗證、去重/冪等策略（idempotency key、去重表、樂觀鎖）
   - 規劃重試/退避、死信佇列、告警
3. **整合與副作用**：
   - 外部呼叫的適配層 (Adapter) 與超時/熔斷/隔離策略
   - 資料一致性策略（Outbox、Transaction Log、批次確認）
4. **產出**：
   - Handler 骨架與介面定義
   - 配置與運維要點（佇列/Topic、重試、死信、監控指標）
   - 驗收測試案例草稿（事件重放、重試、失敗分支）

---

## TypeScript 範例

```typescript
// application/handlers/OrderCreatedHandler.ts

import { EventHandler } from '../ports/EventHandler';
import { IdempotencyService } from '../ports/IdempotencyService';

export interface OrderCreatedEvent {
  readonly eventId: string;
  readonly orderId: string;
  readonly customerId: string;
  readonly items: readonly OrderItemSnapshot[];
  readonly totalAmount: number;
  readonly occurredAt: Date;
}

export class OrderCreatedHandler implements EventHandler<OrderCreatedEvent> {
  constructor(
    private readonly inventoryService: InventoryService,
    private readonly notificationService: NotificationService,
    private readonly idempotencyService: IdempotencyService,
    private readonly logger: Logger,
  ) {}

  async handle(event: OrderCreatedEvent): Promise<void> {
    const idempotencyKey = `order-created:${event.eventId}`;

    // ===== 冪等性檢查 =====
    if (await this.idempotencyService.isDuplicate(idempotencyKey)) {
      this.logger.info('Duplicate event, skipping', { eventId: event.eventId });
      return;
    }

    try {
      // ===== 處理邏輯 =====
      
      // 1. 預留庫存
      await this.inventoryService.reserve({
        orderId: event.orderId,
        items: event.items,
      });

      // 2. 發送通知
      await this.notificationService.sendOrderConfirmation({
        customerId: event.customerId,
        orderId: event.orderId,
        totalAmount: event.totalAmount,
      });

      // ===== 標記處理完成 =====
      await this.idempotencyService.markProcessed(idempotencyKey);

    } catch (error) {
      this.logger.error('Failed to handle OrderCreated', { 
        eventId: event.eventId, 
        error 
      });
      throw error; // 讓 retry 機制接手
    }
  }
}

// 搭配 Retry 與 Dead Letter 的 Consumer
export class OrderEventsConsumer {
  constructor(
    private readonly messageQueue: MessageQueue,
    private readonly orderCreatedHandler: OrderCreatedHandler,
    private readonly deadLetterQueue: DeadLetterQueue,
    private readonly logger: Logger,
  ) {}

  async start(): Promise<void> {
    await this.messageQueue.subscribe('order.created', async (message) => {
      const maxRetries = 3;
      let attempt = 0;

      while (attempt < maxRetries) {
        try {
          const event = this.parseEvent(message);
          await this.orderCreatedHandler.handle(event);
          await message.ack();
          return;
        } catch (error) {
          attempt++;
          this.logger.warn('Retry attempt', { attempt, maxRetries, error });
          
          if (attempt >= maxRetries) {
            // 送入死信佇列
            await this.deadLetterQueue.send({
              originalMessage: message,
              error: error.message,
              attempts: attempt,
            });
            await message.ack(); // 確認以避免無限重試
          } else {
            // 指數退避
            await this.delay(Math.pow(2, attempt) * 1000);
          }
        }
      }
    });
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Go 範例

```go
// application/handler/order_created_handler.go
package handler

import (
    "context"
    "fmt"
    "time"
)

type OrderCreatedEvent struct {
    EventID     string              `json:"event_id"`
    OrderID     string              `json:"order_id"`
    CustomerID  string              `json:"customer_id"`
    Items       []OrderItemSnapshot `json:"items"`
    TotalAmount int64               `json:"total_amount"`
    OccurredAt  time.Time           `json:"occurred_at"`
}

type OrderCreatedHandler struct {
    inventorySvc    InventoryService
    notificationSvc NotificationService
    idempotencySvc  IdempotencyService
    logger          Logger
}

func NewOrderCreatedHandler(
    inventorySvc InventoryService,
    notificationSvc NotificationService,
    idempotencySvc IdempotencyService,
    logger Logger,
) *OrderCreatedHandler {
    return &OrderCreatedHandler{
        inventorySvc:    inventorySvc,
        notificationSvc: notificationSvc,
        idempotencySvc:  idempotencySvc,
        logger:          logger,
    }
}

func (h *OrderCreatedHandler) Handle(ctx context.Context, event OrderCreatedEvent) error {
    idempotencyKey := fmt.Sprintf("order-created:%s", event.EventID)

    // ===== 冪等性檢查 =====
    isDuplicate, err := h.idempotencySvc.IsDuplicate(ctx, idempotencyKey)
    if err != nil {
        return fmt.Errorf("idempotency check failed: %w", err)
    }
    if isDuplicate {
        h.logger.Info("Duplicate event, skipping", "eventId", event.EventID)
        return nil
    }

    // ===== 處理邏輯 =====
    
    // 1. 預留庫存
    if err := h.inventorySvc.Reserve(ctx, ReserveRequest{
        OrderID: event.OrderID,
        Items:   event.Items,
    }); err != nil {
        return fmt.Errorf("failed to reserve inventory: %w", err)
    }

    // 2. 發送通知
    if err := h.notificationSvc.SendOrderConfirmation(ctx, NotificationRequest{
        CustomerID:  event.CustomerID,
        OrderID:     event.OrderID,
        TotalAmount: event.TotalAmount,
    }); err != nil {
        return fmt.Errorf("failed to send notification: %w", err)
    }

    // ===== 標記處理完成 =====
    if err := h.idempotencySvc.MarkProcessed(ctx, idempotencyKey); err != nil {
        h.logger.Warn("Failed to mark as processed", "key", idempotencyKey, "error", err)
    }

    return nil
}

// Consumer with retry and dead letter
type OrderEventsConsumer struct {
    mq                  MessageQueue
    orderCreatedHandler *OrderCreatedHandler
    dlq                 DeadLetterQueue
    logger              Logger
    maxRetries          int
}

func (c *OrderEventsConsumer) Start(ctx context.Context) error {
    return c.mq.Subscribe(ctx, "order.created", func(msg Message) error {
        var event OrderCreatedEvent
        if err := json.Unmarshal(msg.Body, &event); err != nil {
            return c.sendToDeadLetter(msg, err, 0)
        }

        var lastErr error
        for attempt := 1; attempt <= c.maxRetries; attempt++ {
            if err := c.orderCreatedHandler.Handle(ctx, event); err != nil {
                lastErr = err
                c.logger.Warn("Retry attempt", 
                    "attempt", attempt, 
                    "maxRetries", c.maxRetries, 
                    "error", err)
                
                // 指數退避
                time.Sleep(time.Duration(1<<attempt) * time.Second)
                continue
            }
            return nil // 成功
        }

        // 送入死信佇列
        return c.sendToDeadLetter(msg, lastErr, c.maxRetries)
    })
}

func (c *OrderEventsConsumer) sendToDeadLetter(msg Message, err error, attempts int) error {
    return c.dlq.Send(DeadLetterMessage{
        OriginalMessage: msg,
        Error:           err.Error(),
        Attempts:        attempts,
        FailedAt:        time.Now().UTC(),
    })
}
```

---

## 輸出格式
- 程式碼骨架或審查建議，符合 arch-guard、coding-standards、enforce-contract
- 補充 YAML 規格中缺漏的技術約束（佇列名稱、最大重試、超時、冪等鍵來源）

## 檢查清單
- [ ] 是否定義冪等策略並測試重放情境？
- [ ] 重試/退避與死信流程是否清楚？
- [ ] 外部呼叫是否具備超時、熔斷、隔離與觀測 (metrics/log/trace)？
- [ ] 是否處理順序性與一次性需求（若需）？
- [ ] 事件契約是否版本化、向後相容？

## 常見錯誤防範
- ❌ 無冪等導致重放污染狀態
- ❌ 無重試或退避導致雪崩
- ❌ 將外部 SDK 直接放入 Domain 層（違反 arch-guard）
- ❌ 無死信機制導致失敗訊息無限重試
- ❌ 未設定超時導致 Handler 被長時間阻塞

