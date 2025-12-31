# Java Clean Architecture 參考結構

本文件定義 Java 專案的 Clean Architecture 標準結構，基於 Problem Frames 方法論與 DDD 實踐。

## 模組結構

每個 Bounded Context (Aggregate) 獨立為一個模組：

```
src/main/java/com/example/{bounded-context}/
├── {aggregate}/                    # 以 Aggregate 為單位的子模組
│   ├── adapter/                    # Infrastructure Layer
│   │   ├── in/                     # 入站適配器
│   │   │   └── web/                # REST Controllers
│   │   │       └── {Aggregate}Controller.java
│   │   └── out/                    # 出站適配器
│   │       ├── persistence/        # Repository 實作
│   │       │   └── Jpa{Aggregate}Repository.java
│   │       └── projection/         # Read Model / CQRS Query Side
│   │           └── {Aggregate}Projection.java
│   │
│   ├── entity/                     # Domain Layer
│   │   ├── {Aggregate}.java        # Aggregate Root
│   │   ├── {Aggregate}Id.java      # Identity Value Object
│   │   ├── {Aggregate}Events.java  # Domain Events
│   │   ├── {Entity}.java           # Child Entities
│   │   ├── {ValueObject}.java      # Value Objects
│   │   └── {Enum}.java             # Domain Enums
│   │
│   └── usecase/                    # Application Layer
│       ├── port/                   # Ports (Interfaces)
│       │   ├── in/                 # Input Ports (Use Case interfaces)
│       │   │   └── {UseCase}UseCase.java
│       │   └── out/                # Output Ports (Repository interfaces)
│       │       └── {Aggregate}Repository.java
│       │       └── {Aggregate}Mapper.java
│       └── service/                # Use Case Implementations
│           └── {UseCase}Service.java
│
├── common/                         # 共用基礎設施
│   ├── domain/
│   │   ├── AggregateRoot.java
│   │   └── DomainEvent.java
│   └── exception/
│       └── DomainException.java
│
└── io.springboot.config/           # Spring Boot 配置
```

---

## 實際範例：Scrum 專案管理系統

### 模組劃分

```
src/main/java/com/example/scrum/
├── pbi/                            # Product Backlog Item Aggregate
│   ├── adapter.out.projection/
│   ├── entity/
│   │   ├── AcceptanceCriterion.java
│   │   ├── Estimate.java
│   │   ├── EstimatedHours.java
│   │   ├── EstimateType.java (enum)
│   │   ├── Hours.java
│   │   ├── Importance.java
│   │   ├── PbiId.java
│   │   ├── PbiState.java (enum)
│   │   ├── ProductBacklogItem.java  # Aggregate Root
│   │   ├── ProductBacklogItemEvents.java
│   │   ├── RemainingHours.java
│   │   ├── SprintId.java
│   │   ├── TagGroupId.java
│   │   ├── TagId.java
│   │   ├── TagRef.java
│   │   ├── Task.java                # Child Entity
│   │   ├── TaskId.java
│   │   └── TaskState.java (enum)
│   └── usecase/
│       ├── port/
│       │   ├── in/
│       │   └── out/
│       │       └── ProductBacklogItemMapper.java
│       └── service/
│           ├── AddTaskService.java
│           ├── AssignToSprintService.java
│           ├── ChangePbiStateService.java
│           ├── ChangeTaskStateService.java
│           ├── CreateProductBacklogItemService.java
│           ├── DeleteTaskService.java
│           ├── EstimatePbiService.java
│           ├── EstimateTaskService.java
│           ├── GetPbisByProductService.java
│           ├── GetPbisBySprintService.java
│           └── RenameTaskService.java
│
├── product/                        # Product Aggregate
│   ├── adapter.out.projection/
│   ├── entity/
│   └── usecase/
│
├── scrumteam/                      # Scrum Team Aggregate
│   ├── adapter.out.projection/
│   ├── entity/
│   └── usecase/
│       ├── port/
│       └── service/
│           ├── AddScrumTeamMemberService.java
│           ├── CreateScrumTeamService.java
│           ├── DeleteScrumTeamService.java
│           └── GetScrumTeamsService.java
│
└── sprint/                         # Sprint Aggregate
    ├── entity/
    └── usecase/
```

---

## 實作優先順序策略

### 原則

1. **先核心 Aggregate，後支援 Aggregate**
2. **先 Command，後 Query**（或並行）
3. **依相依性順序**：被依賴的先做
4. **完整生命週期**：一個 Aggregate 完成 CRUD 後再換下一個

### 範例優先順序

#### ✅ 已完成 (3)
- `create-product.json` - Product Aggregate 建立
- `create-pbi.json` - PBI Aggregate 建立
- `create-sprint.json` - Sprint Aggregate 建立

#### 1️⃣ Sprint Aggregate (8 remaining) - 完成生命週期

| # | Use Case | Type | Complexity | 說明 |
|---|----------|------|------------|------|
| 1 | start-sprint | Command | Medium | 開始 Sprint |
| 2 | complete-sprint | Command | Medium | 完成 Sprint |
| 3 | cancel-sprint | Command | Low | 取消 Sprint |
| 4 | get-sprint | Query | Low | 查詢單一 Sprint |
| 5 | get-sprints-by-product | Query | Low | 查詢 Product 的 Sprints |
| 6 | define-sprint-goal | Command | Low | 定義 Sprint 目標 |
| 7 | set-sprint-timebox | Command | Low | 設定 Sprint 時間盒 |
| 8 | delete-sprint | Command | Medium | 刪除 Sprint |

#### 2️⃣ Product Aggregate (6 remaining)

| # | Use Case | Type | Complexity |
|---|----------|------|------------|
| 1 | get-product | Query | Low |
| 2 | get-products | Query | Low |
| 3 | set-product-goal | Command | Low |
| 4 | define-dod | Command | Medium |
| 5 | add-product-goal-metric | Command | Medium |
| 6 | delete-product | Command | Medium |

#### 3️⃣ PBI Aggregate (15 remaining) - 最大 backlog

| # | Use Case | Type | Complexity |
|---|----------|------|------------|
| 1 | select-pbi | Command | Medium |
| 2 | unselect-pbi | Command | Low |
| 3 | estimate-pbi | Command | Low |
| 4 | rename-pbi | Command | Low |
| 5 | change-pbi-description | Command | Low |
| 6 | set-acceptance-criteria | Command | Medium |
| 7-15 | Task-related use cases | Mixed | Various |

#### 4️⃣ Scrum Team Aggregate (5 remaining) - 新 Aggregate

| # | Use Case | Type | Complexity |
|---|----------|------|------------|
| 1 | create-scrum-team | Command | Medium (new aggregate) |
| 2 | add-scrum-team-member | Command | Low |
| 3 | get-scrum-teams | Query | Low |
| 4 | get-users | Query | Low |
| 5 | delete-scrum-team | Command | Medium |

---

## Service 命名規範

### Command Side (寫入)

```
{動作}{Aggregate}Service.java

範例：
- CreateProductBacklogItemService
- StartSprintService
- EstimatePbiService
- AddTaskService
- ChangePbiStateService
- DeleteScrumTeamService
```

### Query Side (讀取)

```
Get{Target}Service.java
Get{Target}By{Criteria}Service.java

範例：
- GetPbisByProductService
- GetPbisBySprintService
- GetScrumTeamsService
- GetSprintService
```

---

## Entity 設計規範

### Aggregate Root

```java
@Aggregate
public class ProductBacklogItem {
    private PbiId id;                    // Identity
    private ProductId productId;         // Reference to parent
    private String title;
    private String description;
    private PbiState state;              // Enum state
    private Importance importance;       // Value Object
    private Estimate estimate;           // Value Object
    private SprintId assignedSprintId;   // Nullable reference
    private List<Task> tasks;            // Child entities
    private List<AcceptanceCriterion> acceptanceCriteria;
    
    // Factory method
    public static ProductBacklogItem create(CreatePbiCommand cmd) { ... }
    
    // Business methods
    public void estimate(Estimate estimate) { ... }
    public void assignToSprint(SprintId sprintId) { ... }
    public void addTask(Task task) { ... }
    public void changeState(PbiState newState) { ... }
    
    // Domain events
    private List<DomainEvent> domainEvents = new ArrayList<>();
}
```

### Value Object

```java
@ValueObject
public record Estimate(
    EstimateType type,
    EstimatedHours hours
) {
    public Estimate {
        Objects.requireNonNull(type, "Estimate type is required");
    }
    
    public static Estimate storyPoints(int points) { ... }
    public static Estimate hours(int hours) { ... }
}
```

### Domain Events

```java
public sealed interface ProductBacklogItemEvents {
    
    record PbiCreated(
        PbiId pbiId,
        ProductId productId,
        String title,
        Instant occurredAt
    ) implements ProductBacklogItemEvents {}
    
    record PbiEstimated(
        PbiId pbiId,
        Estimate estimate,
        Instant occurredAt
    ) implements ProductBacklogItemEvents {}
    
    record TaskAdded(
        PbiId pbiId,
        TaskId taskId,
        String taskTitle,
        Instant occurredAt
    ) implements ProductBacklogItemEvents {}
}
```

---

## Use Case Service 模式

```java
@Service
@RequiredArgsConstructor
@Transactional
public class CreateProductBacklogItemService 
        implements CreateProductBacklogItemUseCase {
    
    private final ProductBacklogItemRepository repository;
    private final DomainEventPublisher eventPublisher;
    private final AuthorizationService authService;
    
    @Override
    public Output execute(Input input) {
        // Pre-condition: Authorization
        authService.checkCapability(
            input.operatorId(), 
            "create_pbi", 
            input.productId()
        );
        
        // Domain logic
        var pbi = ProductBacklogItem.create(
            PbiId.generate(),
            ProductId.of(input.productId()),
            input.title(),
            input.description()
        );
        
        // Persist
        repository.save(pbi);
        
        // Publish events
        pbi.getDomainEvents().forEach(eventPublisher::publish);
        
        // Return output
        return new Output(pbi.getId().value());
    }
    
    public record Input(
        String productId,
        String title,
        String description,
        String operatorId
    ) {}
    
    public record Output(String pbiId) {}
}
```

---

## 與 Problem Frames 對應

| Problem Frame | Use Case Type | Service 範例 |
|---------------|---------------|--------------|
| CBF (Command) | Command | CreateProductBacklogItemService |
| IDF (Query) | Query | GetPbisByProductService |
| RIF (Reactor) | EventHandler | PbiCreatedHandler |

### Frame → Service 生成規則

```yaml
# frame.yaml
frame_type: CommandedBehaviorFrame

# 生成
usecase/service/{Feature}Service.java
```

```yaml
# frame.yaml  
frame_type: InformationDisplayFrame

# 生成
usecase/service/Get{Target}Service.java
adapter.out.projection/{Target}Projection.java
```
