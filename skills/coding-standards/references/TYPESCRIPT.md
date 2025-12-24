```markdown
# TypeScript Coding Standards

## 規範 1：Input/Output Type 模式

### 標準模式

```typescript
// application/use-cases/CreateOrderUseCase.ts

// ✅ Input 定義為獨立 type（不可變）
export interface CreateOrderInput {
  readonly customerId: string;
  readonly items: readonly OrderItemRequest[];
  readonly shippingAddress: ShippingAddress;
}

// ✅ Output 定義為獨立 type
export interface CreateOrderOutput {
  readonly orderId: string;
  readonly status: OrderStatus;
  readonly createdAt: Date;
}

// ✅ Use Case 類別
export class CreateOrderUseCase {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly inventoryService: InventoryService,
    private readonly eventPublisher: EventPublisher,
  ) {}

  async execute(input: CreateOrderInput): Promise<CreateOrderOutput> {
    // Pre-conditions
    if (!input.customerId) {
      throw new ValidationError('customerId is required');
    }
    if (!input.items?.length) {
      throw new ValidationError('items must not be empty');
    }

    // Domain logic
    const order = Order.create({
      customerId: new CustomerId(input.customerId),
      items: input.items.map(item => OrderItem.create(item)),
      shippingAddress: input.shippingAddress,
    });

    await this.orderRepository.save(order);
    await this.eventPublisher.publish(new OrderCreatedEvent(order));

    // Post-condition: return immutable output
    return {
      orderId: order.id.value,
      status: order.status,
      createdAt: order.createdAt,
    };
  }
}
```

### 禁止模式

```typescript
// ❌ 禁止：使用 any 或 Record<string, unknown>
async execute(input: Record<string, any>): Promise<any> { }

// ❌ 禁止：直接使用可變物件
export class CreateOrderInput {
  customerId: string;  // 應該是 readonly
  items: OrderItemRequest[];  // 應該是 readonly array
}
```

## 規範 2：依賴注入模式

### 使用工廠函數 (推薦)

```typescript
// infrastructure/factories/useCaseFactory.ts

export function createUseCases(dependencies: Dependencies) {
  return {
    createOrder: new CreateOrderUseCase(
      dependencies.orderRepository,
      dependencies.inventoryService,
      dependencies.eventPublisher,
    ),
    cancelOrder: new CancelOrderUseCase(
      dependencies.orderRepository,
      dependencies.paymentGateway,
    ),
  };
}

// ✅ Use Case 保持純淨，無框架依賴
```

### 使用 DI Container (可選)

```typescript
// infrastructure/container.ts
import { Container } from 'inversify';

const container = new Container();

// ✅ 綁定在 infrastructure 層
container.bind<OrderRepository>(TYPES.OrderRepository)
  .to(PostgresOrderRepository);

container.bind<CreateOrderUseCase>(TYPES.CreateOrderUseCase)
  .toDynamicValue((ctx) => {
    return new CreateOrderUseCase(
      ctx.container.get(TYPES.OrderRepository),
      ctx.container.get(TYPES.InventoryService),
      ctx.container.get(TYPES.EventPublisher),
    );
  });
```

### 禁止模式

```typescript
// ❌ 禁止：在 Use Case 中使用裝飾器注入
@Injectable()  // ❌
export class CreateOrderUseCase {
  @Inject()  // ❌
  private orderRepository: OrderRepository;
}
```

## 規範 3：Value Object 模式

```typescript
// domain/value-objects/OrderId.ts

export class OrderId {
  private readonly _value: string;

  private constructor(value: string) {
    if (!value || value.trim() === '') {
      throw new InvalidOrderIdError('OrderId cannot be empty');
    }
    this._value = value;
  }

  static create(value: string): OrderId {
    return new OrderId(value);
  }

  static generate(): OrderId {
    return new OrderId(crypto.randomUUID());
  }

  get value(): string {
    return this._value;
  }

  equals(other: OrderId): boolean {
    return this._value === other._value;
  }

  toString(): string {
    return this._value;
  }
}
```

## 規範 4：Domain Event 模式

```typescript
// domain/events/OrderCreatedEvent.ts

export interface DomainEvent {
  readonly eventId: string;
  readonly eventType: string;
  readonly aggregateId: string;
  readonly occurredAt: Date;
  readonly version: number;
}

export class OrderCreatedEvent implements DomainEvent {
  readonly eventId: string;
  readonly eventType = 'OrderCreated';
  readonly aggregateId: string;
  readonly occurredAt: Date;
  readonly version: number;

  readonly customerId: string;
  readonly items: readonly OrderItemSnapshot[];
  readonly totalAmount: number;

  constructor(order: Order) {
    this.eventId = crypto.randomUUID();
    this.aggregateId = order.id.value;
    this.occurredAt = new Date();
    this.version = order.version;
    this.customerId = order.customerId.value;
    this.items = order.items.map(item => item.toSnapshot());
    this.totalAmount = order.totalAmount.value;
  }
}
```

## 規範 5：Repository 介面

```typescript
// domain/repositories/OrderRepository.ts

// ✅ 定義在 Domain 層的純介面
export interface OrderRepository {
  findById(id: OrderId): Promise<Order | null>;
  findByCustomerId(customerId: CustomerId): Promise<Order[]>;
  save(order: Order): Promise<void>;
  delete(id: OrderId): Promise<void>;
}

// infrastructure/repositories/PostgresOrderRepository.ts

// ✅ 實作在 Infrastructure 層
export class PostgresOrderRepository implements OrderRepository {
  constructor(private readonly db: Database) {}

  async findById(id: OrderId): Promise<Order | null> {
    const row = await this.db.query(
      'SELECT * FROM orders WHERE id = $1',
      [id.value]
    );
    return row ? this.toDomain(row) : null;
  }

  async save(order: Order): Promise<void> {
    await this.db.query(
      `INSERT INTO orders (id, customer_id, status, total_amount, created_at)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (id) DO UPDATE SET status = $3, total_amount = $4`,
      [order.id.value, order.customerId.value, order.status, order.totalAmount.value, order.createdAt]
    );
  }
}
```

## 規範 6：Error Handling

```typescript
// domain/errors/DomainError.ts

export abstract class DomainError extends Error {
  abstract readonly code: string;
  
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class OrderNotFoundError extends DomainError {
  readonly code = 'ORDER_NOT_FOUND';
  
  constructor(orderId: string) {
    super(`Order not found: ${orderId}`);
  }
}

export class InsufficientInventoryError extends DomainError {
  readonly code = 'INSUFFICIENT_INVENTORY';
  
  constructor(
    public readonly productId: string,
    public readonly requested: number,
    public readonly available: number,
  ) {
    super(`Insufficient inventory for ${productId}: requested ${requested}, available ${available}`);
  }
}
```

## 規範 7：Zod Schema Validation

```typescript
// application/schemas/createOrderSchema.ts
import { z } from 'zod';

export const createOrderInputSchema = z.object({
  customerId: z.string().uuid(),
  items: z.array(z.object({
    productId: z.string().uuid(),
    quantity: z.number().int().positive(),
  })).min(1),
  shippingAddress: z.object({
    street: z.string().min(1),
    city: z.string().min(1),
    postalCode: z.string().regex(/^\d{5}$/),
  }),
});

export type CreateOrderInput = z.infer<typeof createOrderInputSchema>;

// 在 Controller 中使用
export async function createOrderHandler(req: Request): Promise<Response> {
  const parseResult = createOrderInputSchema.safeParse(req.body);
  if (!parseResult.success) {
    return Response.json({ errors: parseResult.error.issues }, { status: 400 });
  }
  
  const result = await createOrderUseCase.execute(parseResult.data);
  return Response.json(result, { status: 201 });
}
```

## 目錄結構

```
src/
├── presentation/           # 展示層
│   ├── http/
│   │   ├── controllers/
│   │   └── middleware/
│   └── graphql/
│
├── application/            # 應用層
│   ├── use-cases/
│   │   ├── CreateOrderUseCase.ts
│   │   └── CancelOrderUseCase.ts
│   ├── queries/
│   │   └── GetOrderByIdQuery.ts
│   ├── schemas/            # Zod schemas
│   └── ports/              # 輸出埠口
│
├── domain/                 # 領域層 (純 TypeScript)
│   ├── aggregates/
│   │   └── Order.ts
│   ├── entities/
│   │   └── OrderItem.ts
│   ├── value-objects/
│   │   ├── OrderId.ts
│   │   └── Money.ts
│   ├── events/
│   │   └── OrderCreatedEvent.ts
│   ├── repositories/       # 介面定義
│   │   └── OrderRepository.ts
│   └── errors/
│       └── DomainError.ts
│
└── infrastructure/         # 基礎設施層
    ├── repositories/       # 實作
    │   └── PostgresOrderRepository.ts
    ├── messaging/
    ├── external/
    └── factories/
        └── useCaseFactory.ts
```

```
