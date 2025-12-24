---
name: query-sub-agent
description: 專責處理 IDF 類型的需求，根據 analyze-frame 輸出的 YAML 規格設計/審查 Query Side（讀模型）與查詢 API。支援 Java、TypeScript、Go 多語言。當需要新增查詢 API、Read Model、報表時使用。
---

# Query Sub-agent Skill

## 觸發時機
- analyze-frame 判定 frame_type=IDF 時
- 需要新增/調整查詢 API、讀模型、報表或搜尋功能時
- 審查查詢效能、投影一致性、快取策略時
- saga-orchestrator 分派 Query 類型任務時

## 核心任務
1. 解析 YAML 規格的查詢目標與接受條件
2. 設計/審查 Query Handler、Read Model、投影與快取策略
3. 確保查詢不造成狀態變更，並對應接受準則 (Given-When-Then)

## Claude Code Sub-agent 整合

本 Skill 可作為 `runSubagent` 的任務目標：

```
saga-orchestrator → runSubagent → query-sub-agent
                                    ├── 讀取 coding-standards
                                    ├── 設計 Read Model
                                    └── 輸出 Query Handler 代碼
```

### 被分派時的輸入格式

```yaml
task:
  type: "query"
  spec_file: "docs/specs/get-order-details.yaml"
  language: "typescript"  # java | typescript | go
  output_path: "src/application/queries/"
```

## 工作流程
1. **解析規格**：讀取 metadata.frame_type=IDF；提取 problem_statement、acceptance_criteria。
2. **查詢設計**：
   - 定義 Query 物件與 Handler（`handle(Query)`）
   - 規劃投影/讀模型（若 CQRS 分離）
   - 確認排序、分頁、過濾、搜尋參數
3. **效能與一致性**：
   - 指定索引需求、N+1 風險、批次查詢策略
   - 規劃快取 (TTL/Key) 與失效策略
4. **產出**：
   - Query Handler 骨架
   - 讀模型/DTO 定義
   - 接受準則對應的查詢測試案例草稿

---

## TypeScript 範例

```typescript
// application/queries/GetOrderByIdQuery.ts

export interface GetOrderByIdInput {
  readonly orderId: string;
}

export interface OrderDetailDto {
  readonly orderId: string;
  readonly customerName: string;
  readonly items: readonly OrderItemDto[];
  readonly totalAmount: number;
  readonly status: OrderStatus;
  readonly createdAt: Date;
}

export class GetOrderByIdQuery {
  constructor(
    private readonly orderReadRepository: OrderReadRepository,
  ) {}

  async execute(input: GetOrderByIdInput): Promise<OrderDetailDto | null> {
    // ===== Pre-conditions =====
    if (!input.orderId) {
      throw new ValidationError('orderId is required');
    }

    // ===== Query (Read-Only) =====
    const order = await this.orderReadRepository.findDetailById(input.orderId);
    
    if (!order) {
      return null;
    }

    // ===== Map to DTO =====
    return {
      orderId: order.id,
      customerName: order.customerName,
      items: order.items.map(item => ({
        productName: item.productName,
        quantity: item.quantity,
        price: item.price,
      })),
      totalAmount: order.totalAmount,
      status: order.status,
      createdAt: order.createdAt,
    };
  }
}

// 分頁查詢範例
export interface ListOrdersInput {
  readonly customerId?: string;
  readonly status?: OrderStatus;
  readonly page: number;
  readonly pageSize: number;
  readonly sortBy?: 'createdAt' | 'totalAmount';
  readonly sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResult<T> {
  readonly items: readonly T[];
  readonly total: number;
  readonly page: number;
  readonly pageSize: number;
  readonly hasNext: boolean;
}

export class ListOrdersQuery {
  constructor(
    private readonly orderReadRepository: OrderReadRepository,
    private readonly cache: CacheService,
  ) {}

  async execute(input: ListOrdersInput): Promise<PaginatedResult<OrderSummaryDto>> {
    // ===== Validation =====
    const pageSize = Math.min(input.pageSize, 100); // 限制最大筆數
    const page = Math.max(input.page, 1);

    // ===== Cache Check =====
    const cacheKey = this.buildCacheKey(input);
    const cached = await this.cache.get<PaginatedResult<OrderSummaryDto>>(cacheKey);
    if (cached) {
      return cached;
    }

    // ===== Query =====
    const result = await this.orderReadRepository.findOrders({
      customerId: input.customerId,
      status: input.status,
      offset: (page - 1) * pageSize,
      limit: pageSize,
      sortBy: input.sortBy ?? 'createdAt',
      sortOrder: input.sortOrder ?? 'desc',
    });

    const response: PaginatedResult<OrderSummaryDto> = {
      items: result.items,
      total: result.total,
      page,
      pageSize,
      hasNext: page * pageSize < result.total,
    };

    // ===== Cache Result =====
    await this.cache.set(cacheKey, response, { ttl: 60 }); // 60 seconds

    return response;
  }
}
```

## Go 範例

```go
// application/query/get_order.go
package query

type GetOrderByIdInput struct {
    OrderID string `json:"order_id" validate:"required,uuid"`
}

type OrderDetailDto struct {
    OrderID      string         `json:"order_id"`
    CustomerName string         `json:"customer_name"`
    Items        []OrderItemDto `json:"items"`
    TotalAmount  int64          `json:"total_amount"`
    Status       string         `json:"status"`
    CreatedAt    time.Time      `json:"created_at"`
}

type GetOrderByIdQuery struct {
    orderReadRepo OrderReadRepository
}

func NewGetOrderByIdQuery(orderReadRepo OrderReadRepository) *GetOrderByIdQuery {
    return &GetOrderByIdQuery{orderReadRepo: orderReadRepo}
}

func (q *GetOrderByIdQuery) Execute(ctx context.Context, input GetOrderByIdInput) (*OrderDetailDto, error) {
    // ===== Pre-conditions =====
    if err := ValidateInput(input); err != nil {
        return nil, err
    }

    // ===== Query (Read-Only) =====
    order, err := q.orderReadRepo.FindDetailByID(ctx, input.OrderID)
    if err != nil {
        return nil, err
    }
    if order == nil {
        return nil, nil // or ErrOrderNotFound
    }

    // ===== Map to DTO =====
    return &OrderDetailDto{
        OrderID:      order.ID,
        CustomerName: order.CustomerName,
        Items:        mapToItemDtos(order.Items),
        TotalAmount:  order.TotalAmount,
        Status:       order.Status,
        CreatedAt:    order.CreatedAt,
    }, nil
}

// 分頁查詢
type ListOrdersInput struct {
    CustomerID *string     `json:"customer_id"`
    Status     *string     `json:"status"`
    Page       int         `json:"page" validate:"required,min=1"`
    PageSize   int         `json:"page_size" validate:"required,min=1,max=100"`
    SortBy     string      `json:"sort_by"`
    SortOrder  string      `json:"sort_order"`
}

type PaginatedResult[T any] struct {
    Items    []T   `json:"items"`
    Total    int64 `json:"total"`
    Page     int   `json:"page"`
    PageSize int   `json:"page_size"`
    HasNext  bool  `json:"has_next"`
}

type ListOrdersQuery struct {
    orderReadRepo OrderReadRepository
    cache         CacheService
}

func (q *ListOrdersQuery) Execute(ctx context.Context, input ListOrdersInput) (*PaginatedResult[OrderSummaryDto], error) {
    // ===== Limit page size =====
    pageSize := min(input.PageSize, 100)
    
    // ===== Query =====
    result, err := q.orderReadRepo.FindOrders(ctx, FindOrdersParams{
        CustomerID: input.CustomerID,
        Status:     input.Status,
        Offset:     (input.Page - 1) * pageSize,
        Limit:      pageSize,
        SortBy:     input.SortBy,
        SortOrder:  input.SortOrder,
    })
    if err != nil {
        return nil, err
    }

    return &PaginatedResult[OrderSummaryDto]{
        Items:    result.Items,
        Total:    result.Total,
        Page:     input.Page,
        PageSize: pageSize,
        HasNext:  int64(input.Page*pageSize) < result.Total,
    }, nil
}
```

---

## 輸出格式
- 程式碼骨架或審查建議，需符合 arch-guard、coding-standards、enforce-contract
- 若規格缺漏，回寫補充建議（例如：排序欄位、分頁限制、最大筆數）

## 檢查清單
- [ ] Query Handler 僅做讀取，無狀態變更？
- [ ] 是否提供分頁、排序、過濾與輸入驗證？
- [ ] N+1 或大查詢風險是否已處理（批次/索引）？
- [ ] 是否設計快取策略並規範失效機制？
- [ ] DTO/Read Model 是否與 Domain 解耦？
- [ ] 錯誤情境（查無資料/權限）是否明確？

## 常見錯誤防範
- ❌ 在 Query Handler 中修改狀態或發布事件
- ❌ 未限制分頁大小導致全表掃描
- ❌ 查詢結果直接回傳 Entity，導致洩漏內部模型
- ❌ 未考慮快取失效策略導致資料不一致

