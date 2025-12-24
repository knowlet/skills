---
name: command-sub-agent
description: 專責處理 CBF 類型的需求，接收 analyze-frame 輸出的 YAML 規格，生成/審查 Command Side 設計與實作。支援 Java、TypeScript、Go 多語言。當需要建立/修改寫模型的 Use Case、Aggregate、Domain Event 時使用。
---

# Command Sub-agent Skill

## 觸發時機
- analyze-frame 判定 frame_type=CBF 時
- 需要建立/修改 Command Side (寫模型) 的用例、聚合、事件時
- 生成或審查變更狀態的 API / Handler / Use Case 時
- saga-orchestrator 分派 Command 類型任務時

## 核心任務
1. 解析 YAML 規格中的 Command 類資訊
2. 設計/驗證 CQRS Command Side 的用例、聚合與事件流
3. 產出程式碼骨架或審查既有實作，確保寫入流程正確、可測且具備事件發布

## Claude Code Sub-agent 整合

本 Skill 可作為 `runSubagent` 的任務目標，接收來自 saga-orchestrator 的分派：

```
saga-orchestrator → runSubagent → command-sub-agent
                                    ├── 讀取 coding-standards
                                    ├── 讀取 enforce-contract  
                                    └── 輸出 Command Side 代碼
```

### 被分派時的輸入格式

```yaml
task:
  type: "command"
  spec_file: "docs/specs/create-order.yaml"
  language: "typescript"  # java | typescript | go
  output_path: "src/application/use-cases/"
```

## 工作流程
1. **解析規格**：讀取 metadata.frame_type=CBF 與 sub_agent=command-sub-agent；提取 problem_statement、domain、acceptance_criteria。
2. **用例建模**：對應 `UseCase` 或 `CommandHandler`，套用 Input/Output 模式與不可變物件規範。
3. **聚合設計**：確認 Aggregate root、Entities、Value Objects、Domain Events；維護 invariants。
4. **流程編排**：
   - 前置驗證 (pre-conditions)
   - 執行狀態變更 (domain logic)
   - 發布 Domain Events
   - 持久化 (透過 Repository 介面)
5. **產出**：
   - 程式碼骨架（Application/Domain 層）
   - 事件定義與發布點
   - 驗收測試案例（Given-When-Then）草稿

---

## TypeScript 範例

```typescript
// application/use-cases/CreateOrderUseCase.ts

export interface CreateOrderInput {
  readonly customerId: string;
  readonly items: readonly OrderItemRequest[];
  readonly shippingAddress: ShippingAddress;
}

export interface CreateOrderOutput {
  readonly orderId: string;
  readonly status: OrderStatus;
  readonly createdAt: Date;
}

export class CreateOrderUseCase {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly inventoryService: InventoryService,
    private readonly eventPublisher: EventPublisher,
  ) {}

  async execute(input: CreateOrderInput): Promise<CreateOrderOutput> {
    // ===== Pre-conditions =====
    if (!input.customerId) {
      throw new ValidationError('customerId is required');
    }
    if (!input.items?.length) {
      throw new ValidationError('items must not be empty');
    }

    // ===== Domain Logic =====
    const order = Order.create({
      customerId: new CustomerId(input.customerId),
      items: input.items.map(i => OrderItem.create(i)),
      shippingAddress: input.shippingAddress,
    });

    // ===== Persist =====
    await this.orderRepository.save(order);

    // ===== Publish Domain Event =====
    await this.eventPublisher.publish(new OrderCreatedEvent(order));

    // ===== Post-conditions =====
    return {
      orderId: order.id.value,
      status: order.status,
      createdAt: order.createdAt,
    };
  }
}
```

## Go 範例

```go
// application/usecase/create_order.go
package usecase

type CreateOrderInput struct {
    CustomerID      string           `json:"customer_id" validate:"required,uuid"`
    Items           []OrderItemInput `json:"items" validate:"required,min=1,dive"`
    ShippingAddress Address          `json:"shipping_address" validate:"required"`
}

type CreateOrderOutput struct {
    OrderID   string      `json:"order_id"`
    Status    OrderStatus `json:"status"`
    CreatedAt time.Time   `json:"created_at"`
}

type CreateOrderUseCase struct {
    orderRepo    OrderRepository
    inventorySvc InventoryService
    eventPub     EventPublisher
}

func NewCreateOrderUseCase(
    orderRepo OrderRepository,
    inventorySvc InventoryService,
    eventPub EventPublisher,
) *CreateOrderUseCase {
    return &CreateOrderUseCase{
        orderRepo:    orderRepo,
        inventorySvc: inventorySvc,
        eventPub:     eventPub,
    }
}

func (uc *CreateOrderUseCase) Execute(ctx context.Context, input CreateOrderInput) (*CreateOrderOutput, error) {
    // ===== Pre-conditions =====
    if err := ValidateInput(input); err != nil {
        return nil, err
    }

    // ===== Domain Logic =====
    order, err := domain.NewOrder(
        domain.NewCustomerID(input.CustomerID),
        mapToOrderItems(input.Items),
        input.ShippingAddress,
    )
    if err != nil {
        return nil, err
    }

    // ===== Persist =====
    if err := uc.orderRepo.Save(ctx, order); err != nil {
        return nil, err
    }

    // ===== Publish Domain Event =====
    if err := uc.eventPub.Publish(ctx, domain.NewOrderCreatedEvent(order)); err != nil {
        return nil, err
    }

    return &CreateOrderOutput{
        OrderID:   order.ID().String(),
        Status:    order.Status(),
        CreatedAt: order.CreatedAt(),
    }, nil
}
```

---

## 輸出格式
- 主要輸出：程式碼骨架或審查建議（遵守 arch-guard、coding-standards、enforce-contract）
- 次要輸出：對 YAML 規格的補充或修正建議（若缺欄位）

## 檢查清單
- [ ] 是否使用 Input/Output 模式並保持不可變？
- [ ] pre-conditions 是否完整覆蓋邊界情況？
- [ ] Domain invariants 是否在變更後仍成立？
- [ ] 是否發布正確的 Domain Events？
- [ ] Repository 介面是否位於 Domain，實作位於 Infrastructure？
- [ ] 是否避免在 Domain 直接依賴框架 (遵守 arch-guard)？

## 常見錯誤防範
- ❌ 在 Domain/UseCase 中使用框架註解（Java: @Component/@Service, TS: @Injectable）
- ❌ 忽略事件的冪等性/重試策略
- ❌ 在 Use Case 中混入查詢邏輯（應留給 query-sub-agent）
- ❌ 使用可變的 Input/Output 物件

