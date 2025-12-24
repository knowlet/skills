```markdown
# Go Coding Standards

## 規範 1：Input/Output Struct 模式

### 標準模式

```go
// application/usecase/create_order.go
package usecase

import (
    "context"
    "time"
)

// ✅ Input 定義為獨立 struct
type CreateOrderInput struct {
    CustomerID      string           `json:"customer_id" validate:"required,uuid"`
    Items           []OrderItemInput `json:"items" validate:"required,min=1,dive"`
    ShippingAddress Address          `json:"shipping_address" validate:"required"`
}

type OrderItemInput struct {
    ProductID string `json:"product_id" validate:"required,uuid"`
    Quantity  int    `json:"quantity" validate:"required,gt=0"`
}

// ✅ Output 定義為獨立 struct
type CreateOrderOutput struct {
    OrderID   string      `json:"order_id"`
    Status    OrderStatus `json:"status"`
    CreatedAt time.Time   `json:"created_at"`
}

// ✅ Use Case 結構
type CreateOrderUseCase struct {
    orderRepo     OrderRepository
    inventorySvc  InventoryService
    eventPub      EventPublisher
}

// ✅ 使用建構子注入依賴
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

// ✅ Execute 方法接收 Input，回傳 Output
func (uc *CreateOrderUseCase) Execute(ctx context.Context, input CreateOrderInput) (*CreateOrderOutput, error) {
    // Pre-conditions
    if input.CustomerID == "" {
        return nil, NewValidationError("customer_id is required")
    }
    if len(input.Items) == 0 {
        return nil, NewValidationError("items must not be empty")
    }

    // Domain logic
    order, err := domain.NewOrder(
        domain.NewCustomerID(input.CustomerID),
        mapToOrderItems(input.Items),
        input.ShippingAddress,
    )
    if err != nil {
        return nil, err
    }

    if err := uc.orderRepo.Save(ctx, order); err != nil {
        return nil, err
    }

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

### 禁止模式

```go
// ❌ 禁止：使用 map[string]interface{}
func (uc *CreateOrderUseCase) Execute(ctx context.Context, input map[string]interface{}) (map[string]interface{}, error)

// ❌ 禁止：直接使用多個參數
func (uc *CreateOrderUseCase) Execute(ctx context.Context, customerID string, items []Item, address string) (*Order, error)
```

## 規範 2：依賴注入模式

### 使用 Wire (推薦)

```go
// infrastructure/wire.go
//go:build wireinject
// +build wireinject

package infrastructure

import (
    "github.com/google/wire"
)

func InitializeApp() (*App, error) {
    wire.Build(
        // Repositories
        NewPostgresOrderRepository,
        wire.Bind(new(usecase.OrderRepository), new(*PostgresOrderRepository)),
        
        // Services
        NewInventoryService,
        wire.Bind(new(usecase.InventoryService), new(*InventoryService)),
        
        // Event Publisher
        NewKafkaEventPublisher,
        wire.Bind(new(usecase.EventPublisher), new(*KafkaEventPublisher)),
        
        // Use Cases
        usecase.NewCreateOrderUseCase,
        usecase.NewCancelOrderUseCase,
        
        // App
        NewApp,
    )
    return nil, nil
}
```

### 手動組裝 (簡單專案)

```go
// cmd/main.go
func main() {
    // Infrastructure
    db := postgres.NewConnection(cfg.DatabaseURL)
    kafka := messaging.NewKafkaClient(cfg.KafkaURL)
    
    // Repositories
    orderRepo := repository.NewPostgresOrderRepository(db)
    
    // Services
    inventorySvc := service.NewInventoryService(db)
    eventPub := messaging.NewKafkaEventPublisher(kafka)
    
    // Use Cases
    createOrderUC := usecase.NewCreateOrderUseCase(orderRepo, inventorySvc, eventPub)
    cancelOrderUC := usecase.NewCancelOrderUseCase(orderRepo)
    
    // HTTP Handlers
    handler := http.NewHandler(createOrderUC, cancelOrderUC)
    
    // Start server
    server := http.NewServer(handler)
    server.Run(":8080")
}
```

## 規範 3：Value Object 模式

```go
// domain/value_object/order_id.go
package valueobject

import (
    "errors"
    "github.com/google/uuid"
)

var ErrInvalidOrderID = errors.New("invalid order id")

type OrderID struct {
    value string
}

func NewOrderID(value string) (OrderID, error) {
    if value == "" {
        return OrderID{}, ErrInvalidOrderID
    }
    if _, err := uuid.Parse(value); err != nil {
        return OrderID{}, ErrInvalidOrderID
    }
    return OrderID{value: value}, nil
}

func GenerateOrderID() OrderID {
    return OrderID{value: uuid.New().String()}
}

func (id OrderID) String() string {
    return id.value
}

func (id OrderID) Equals(other OrderID) bool {
    return id.value == other.value
}

func (id OrderID) IsZero() bool {
    return id.value == ""
}
```

## 規範 4：Domain Event 模式

```go
// domain/event/order_created.go
package event

import (
    "time"
    "github.com/google/uuid"
)

type DomainEvent interface {
    EventID() string
    EventType() string
    AggregateID() string
    OccurredAt() time.Time
    Version() int
}

type OrderCreatedEvent struct {
    eventID     string
    aggregateID string
    occurredAt  time.Time
    version     int
    
    CustomerID  string
    Items       []OrderItemSnapshot
    TotalAmount int64
}

func NewOrderCreatedEvent(order *Order) *OrderCreatedEvent {
    return &OrderCreatedEvent{
        eventID:     uuid.New().String(),
        aggregateID: order.ID().String(),
        occurredAt:  time.Now().UTC(),
        version:     order.Version(),
        CustomerID:  order.CustomerID().String(),
        Items:       order.ItemSnapshots(),
        TotalAmount: order.TotalAmount().Cents(),
    }
}

func (e *OrderCreatedEvent) EventID() string     { return e.eventID }
func (e *OrderCreatedEvent) EventType() string   { return "OrderCreated" }
func (e *OrderCreatedEvent) AggregateID() string { return e.aggregateID }
func (e *OrderCreatedEvent) OccurredAt() time.Time { return e.occurredAt }
func (e *OrderCreatedEvent) Version() int        { return e.version }
```

## 規範 5：Repository 介面

```go
// domain/repository/order_repository.go
package repository

import (
    "context"
)

// ✅ 定義在 Domain 層的介面
type OrderRepository interface {
    FindByID(ctx context.Context, id valueobject.OrderID) (*aggregate.Order, error)
    FindByCustomerID(ctx context.Context, customerID valueobject.CustomerID) ([]*aggregate.Order, error)
    Save(ctx context.Context, order *aggregate.Order) error
    Delete(ctx context.Context, id valueobject.OrderID) error
}

// infrastructure/repository/postgres_order_repository.go

// ✅ 實作在 Infrastructure 層
type PostgresOrderRepository struct {
    db *sql.DB
}

func NewPostgresOrderRepository(db *sql.DB) *PostgresOrderRepository {
    return &PostgresOrderRepository{db: db}
}

func (r *PostgresOrderRepository) FindByID(ctx context.Context, id valueobject.OrderID) (*aggregate.Order, error) {
    row := r.db.QueryRowContext(ctx,
        `SELECT id, customer_id, status, total_amount, created_at 
         FROM orders WHERE id = $1`,
        id.String(),
    )
    return r.scanOrder(row)
}

func (r *PostgresOrderRepository) Save(ctx context.Context, order *aggregate.Order) error {
    _, err := r.db.ExecContext(ctx,
        `INSERT INTO orders (id, customer_id, status, total_amount, created_at)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (id) DO UPDATE SET status = $3, total_amount = $4`,
        order.ID().String(),
        order.CustomerID().String(),
        order.Status(),
        order.TotalAmount().Cents(),
        order.CreatedAt(),
    )
    return err
}
```

## 規範 6：Error Handling

```go
// domain/error/domain_error.go
package domainerror

import "fmt"

type DomainError struct {
    Code    string
    Message string
    Err     error
}

func (e *DomainError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func (e *DomainError) Unwrap() error {
    return e.Err
}

// 預定義錯誤
var (
    ErrOrderNotFound = &DomainError{
        Code:    "ORDER_NOT_FOUND",
        Message: "order not found",
    }
)

func NewOrderNotFoundError(orderID string) *DomainError {
    return &DomainError{
        Code:    "ORDER_NOT_FOUND",
        Message: fmt.Sprintf("order not found: %s", orderID),
    }
}

func NewInsufficientInventoryError(productID string, requested, available int) *DomainError {
    return &DomainError{
        Code:    "INSUFFICIENT_INVENTORY",
        Message: fmt.Sprintf("insufficient inventory for %s: requested %d, available %d", 
            productID, requested, available),
    }
}
```

## 規範 7：Validation (使用 go-playground/validator)

```go
// application/usecase/validation.go
package usecase

import (
    "github.com/go-playground/validator/v10"
)

var validate = validator.New()

func ValidateInput(input interface{}) error {
    if err := validate.Struct(input); err != nil {
        return NewValidationError(err.Error())
    }
    return nil
}

// 使用範例
func (uc *CreateOrderUseCase) Execute(ctx context.Context, input CreateOrderInput) (*CreateOrderOutput, error) {
    if err := ValidateInput(input); err != nil {
        return nil, err
    }
    // ...
}
```

## 目錄結構

```
.
├── cmd/
│   └── api/
│       └── main.go              # 應用程式入口
│
├── internal/
│   ├── presentation/            # 展示層
│   │   ├── http/
│   │   │   ├── handler/
│   │   │   ├── middleware/
│   │   │   └── router.go
│   │   └── grpc/
│   │
│   ├── application/             # 應用層
│   │   ├── usecase/
│   │   │   ├── create_order.go
│   │   │   └── cancel_order.go
│   │   └── query/
│   │       └── get_order.go
│   │
│   ├── domain/                  # 領域層 (純 Go)
│   │   ├── aggregate/
│   │   │   └── order.go
│   │   ├── entity/
│   │   │   └── order_item.go
│   │   ├── valueobject/
│   │   │   ├── order_id.go
│   │   │   └── money.go
│   │   ├── event/
│   │   │   └── order_created.go
│   │   ├── repository/          # 介面定義
│   │   │   └── order_repository.go
│   │   └── error/
│   │       └── domain_error.go
│   │
│   └── infrastructure/          # 基礎設施層
│       ├── repository/          # 實作
│       │   └── postgres_order_repository.go
│       ├── messaging/
│       │   └── kafka_publisher.go
│       ├── external/
│       └── config/
│
├── pkg/                         # 可共用的套件
│
├── go.mod
└── go.sum
```

```
