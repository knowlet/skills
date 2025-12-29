# Rust Coding Standards

本文件定義 Rust 專案的編碼規範，基於 Problem Frames 方法論，確保 AI 生成的代碼風格一致。

## 專案結構

```
project-name/
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── lib.rs                 # Library crate root
│   ├── main.rs                # Binary crate entry (if applicable)
│   │
│   ├── application/           # Application Layer (Use Cases)
│   │   ├── mod.rs
│   │   ├── use_cases/
│   │   │   ├── mod.rs
│   │   │   ├── create_workflow.rs
│   │   │   └── query_workflow.rs
│   │   └── ports/             # Input/Output ports (interfaces)
│   │       ├── mod.rs
│   │       └── workflow_repository.rs
│   │
│   ├── domain/                # Domain Layer (Entities, Value Objects)
│   │   ├── mod.rs
│   │   ├── aggregates/
│   │   │   ├── mod.rs
│   │   │   └── workflow.rs
│   │   ├── value_objects/
│   │   │   ├── mod.rs
│   │   │   ├── workflow_id.rs
│   │   │   └── workflow_name.rs
│   │   ├── events/
│   │   │   ├── mod.rs
│   │   │   └── workflow_events.rs
│   │   └── errors.rs
│   │
│   └── infrastructure/        # Infrastructure Layer
│       ├── mod.rs
│       ├── repositories/
│       │   ├── mod.rs
│       │   └── postgres_workflow_repository.rs
│       ├── adapters/          # ACL implementations
│       │   ├── mod.rs
│       │   └── access_control_adapter.rs
│       └── web/               # HTTP handlers
│           ├── mod.rs
│           └── workflow_controller.rs
│
└── tests/
    ├── common/                # Shared test utilities
    │   └── mod.rs
    ├── unit/
    ├── integration/
    └── acceptance/
        └── create_workflow.rs
```

---

## 規範 1：Input/Output Struct 模式

### Use Case 結構

```rust
// src/application/use_cases/create_workflow.rs

use crate::domain::{Workflow, WorkflowId, WorkflowName, BoardId};
use crate::domain::events::WorkflowCreatedEvent;
use crate::domain::errors::DomainError;
use crate::application::ports::{WorkflowRepository, EventPublisher, AuthorizationService};
use std::sync::Arc;

/// Input for creating a workflow
/// 
/// # Invariants
/// - `board_id` must be a valid UUID
/// - `name` must not be empty and <= 255 characters
#[derive(Debug, Clone)]
pub struct CreateWorkflowInput {
    pub board_id: String,
    pub name: String,
    pub operator_id: String,
}

impl CreateWorkflowInput {
    /// Validates and creates a new input
    pub fn new(board_id: String, name: String, operator_id: String) -> Result<Self, DomainError> {
        if board_id.is_empty() {
            return Err(DomainError::validation("board_id is required"));
        }
        if name.is_empty() {
            return Err(DomainError::validation("name is required"));
        }
        if name.len() > 255 {
            return Err(DomainError::validation("name exceeds max length"));
        }
        
        Ok(Self { board_id, name, operator_id })
    }
}

/// Output from creating a workflow
#[derive(Debug, Clone)]
pub struct CreateWorkflowOutput {
    pub workflow_id: String,
    pub board_id: String,
    pub name: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

/// Use Case for creating a workflow
/// 
/// # Frame Type
/// CommandedBehaviorFrame (CBF)
/// 
/// # Frame Concerns
/// - FC1: Authorization - checked via AuthorizationService
/// - FC2: Event Publishing - WorkflowCreatedEvent published
pub struct CreateWorkflowUseCase<R, E, A>
where
    R: WorkflowRepository,
    E: EventPublisher,
    A: AuthorizationService,
{
    repository: Arc<R>,
    event_publisher: Arc<E>,
    auth_service: Arc<A>,
}

impl<R, E, A> CreateWorkflowUseCase<R, E, A>
where
    R: WorkflowRepository,
    E: EventPublisher,
    A: AuthorizationService,
{
    pub fn new(
        repository: Arc<R>,
        event_publisher: Arc<E>,
        auth_service: Arc<A>,
    ) -> Self {
        Self {
            repository,
            event_publisher,
            auth_service,
        }
    }

    /// Executes the use case
    /// 
    /// # Pre-conditions
    /// - Operator must be authorized to create workflows for the board
    /// 
    /// # Post-conditions
    /// - Workflow is persisted
    /// - WorkflowCreatedEvent is published
    pub async fn execute(&self, input: CreateWorkflowInput) -> Result<CreateWorkflowOutput, DomainError> {
        // Pre-condition: Authorization check
        self.auth_service
            .check_capability(&input.operator_id, "create_workflow", &input.board_id)
            .await
            .map_err(|_| DomainError::unauthorized("Not authorized to create workflow"))?;

        // Domain logic
        let workflow_id = WorkflowId::new();
        let board_id = BoardId::parse(&input.board_id)?;
        let name = WorkflowName::new(&input.name)?;
        
        let workflow = Workflow::create(workflow_id.clone(), board_id, name)?;
        
        // Persist
        self.repository.save(&workflow).await?;
        
        // Publish event
        let event = WorkflowCreatedEvent {
            workflow_id: workflow_id.to_string(),
            board_id: input.board_id.clone(),
            name: input.name.clone(),
            occurred_at: chrono::Utc::now(),
        };
        self.event_publisher.publish(event).await?;
        
        // Post-condition satisfied
        Ok(CreateWorkflowOutput {
            workflow_id: workflow_id.to_string(),
            board_id: input.board_id,
            name: input.name,
            created_at: chrono::Utc::now(),
        })
    }
}
```

---

## 規範 2：Value Objects

### 不可變性與驗證

```rust
// src/domain/value_objects/workflow_id.rs

use std::fmt;
use uuid::Uuid;
use crate::domain::errors::DomainError;

/// Workflow identifier
/// 
/// # Invariants
/// - Must be a valid UUID v4
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct WorkflowId(Uuid);

impl WorkflowId {
    /// Creates a new random WorkflowId
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    /// Parses a WorkflowId from string
    pub fn parse(s: &str) -> Result<Self, DomainError> {
        Uuid::parse_str(s)
            .map(Self)
            .map_err(|_| DomainError::validation("Invalid workflow ID format"))
    }

    /// Returns the inner UUID
    pub fn value(&self) -> &Uuid {
        &self.0
    }
}

impl Default for WorkflowId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for WorkflowId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl From<WorkflowId> for String {
    fn from(id: WorkflowId) -> Self {
        id.0.to_string()
    }
}
```

```rust
// src/domain/value_objects/workflow_name.rs

use crate::domain::errors::DomainError;

/// Workflow name with validation
/// 
/// # Invariants
/// - Must not be empty
/// - Must not exceed 255 characters
/// - Must not contain only whitespace
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorkflowName(String);

impl WorkflowName {
    const MAX_LENGTH: usize = 255;

    pub fn new(name: &str) -> Result<Self, DomainError> {
        let trimmed = name.trim();
        
        if trimmed.is_empty() {
            return Err(DomainError::validation("Workflow name cannot be empty"));
        }
        
        if trimmed.len() > Self::MAX_LENGTH {
            return Err(DomainError::validation(format!(
                "Workflow name cannot exceed {} characters",
                Self::MAX_LENGTH
            )));
        }
        
        Ok(Self(trimmed.to_string()))
    }

    pub fn value(&self) -> &str {
        &self.0
    }
}

impl AsRef<str> for WorkflowName {
    fn as_ref(&self) -> &str {
        &self.0
    }
}
```

---

## 規範 3：Aggregate Root

```rust
// src/domain/aggregates/workflow.rs

use crate::domain::value_objects::{WorkflowId, WorkflowName, BoardId};
use crate::domain::errors::DomainError;
use chrono::{DateTime, Utc};

/// Workflow aggregate root
/// 
/// # Invariants
/// - Must belong to a board
/// - Name must be valid
/// - Cannot be modified after deletion
#[derive(Debug, Clone)]
pub struct Workflow {
    id: WorkflowId,
    board_id: BoardId,
    name: WorkflowName,
    is_deleted: bool,
    stages: Vec<StageId>,
    lanes: Vec<LaneId>,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
}

impl Workflow {
    /// Creates a new workflow
    /// 
    /// # Invariants enforced
    /// - Starts with empty stages and lanes
    /// - is_deleted = false
    pub fn create(
        id: WorkflowId,
        board_id: BoardId,
        name: WorkflowName,
    ) -> Result<Self, DomainError> {
        let now = Utc::now();
        
        Ok(Self {
            id,
            board_id,
            name,
            is_deleted: false,
            stages: Vec::new(),
            lanes: Vec::new(),
            created_at: now,
            updated_at: now,
        })
    }

    /// Renames the workflow
    /// 
    /// # Pre-conditions
    /// - Workflow must not be deleted
    pub fn rename(&mut self, new_name: WorkflowName) -> Result<(), DomainError> {
        self.ensure_not_deleted()?;
        self.name = new_name;
        self.updated_at = Utc::now();
        Ok(())
    }

    /// Soft-deletes the workflow
    pub fn delete(&mut self) -> Result<(), DomainError> {
        self.ensure_not_deleted()?;
        self.is_deleted = true;
        self.updated_at = Utc::now();
        Ok(())
    }

    // ===== Query Methods =====
    
    pub fn id(&self) -> &WorkflowId {
        &self.id
    }

    pub fn board_id(&self) -> &BoardId {
        &self.board_id
    }

    pub fn name(&self) -> &WorkflowName {
        &self.name
    }

    pub fn is_deleted(&self) -> bool {
        self.is_deleted
    }

    pub fn stages(&self) -> &[StageId] {
        &self.stages
    }

    pub fn lanes(&self) -> &[LaneId] {
        &self.lanes
    }

    // ===== Private Invariant Checks =====

    fn ensure_not_deleted(&self) -> Result<(), DomainError> {
        if self.is_deleted {
            return Err(DomainError::invalid_state("Workflow is deleted"));
        }
        Ok(())
    }
}
```

---

## 規範 4：Repository Trait (Port)

```rust
// src/application/ports/workflow_repository.rs

use async_trait::async_trait;
use crate::domain::{Workflow, WorkflowId, BoardId};
use crate::domain::errors::DomainError;

/// Repository port for Workflow aggregate
/// 
/// Implemented by infrastructure layer
#[async_trait]
pub trait WorkflowRepository: Send + Sync {
    /// Saves a workflow (insert or update)
    async fn save(&self, workflow: &Workflow) -> Result<(), DomainError>;

    /// Finds a workflow by ID
    async fn find_by_id(&self, id: &WorkflowId) -> Result<Option<Workflow>, DomainError>;

    /// Finds all workflows for a board
    async fn find_by_board_id(&self, board_id: &BoardId) -> Result<Vec<Workflow>, DomainError>;

    /// Deletes a workflow (hard delete, use sparingly)
    async fn delete(&self, id: &WorkflowId) -> Result<(), DomainError>;

    /// Checks if a workflow exists
    async fn exists(&self, id: &WorkflowId) -> Result<bool, DomainError>;
}
```

---

## 規範 5：Error Handling

```rust
// src/domain/errors.rs

use thiserror::Error;

/// Domain errors
#[derive(Debug, Error)]
pub enum DomainError {
    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Invalid state: {0}")]
    InvalidState(String),

    #[error("Conflict: {0}")]
    Conflict(String),

    #[error("Infrastructure error: {0}")]
    Infrastructure(String),
}

impl DomainError {
    pub fn validation(msg: impl Into<String>) -> Self {
        Self::Validation(msg.into())
    }

    pub fn not_found(msg: impl Into<String>) -> Self {
        Self::NotFound(msg.into())
    }

    pub fn unauthorized(msg: impl Into<String>) -> Self {
        Self::Unauthorized(msg.into())
    }

    pub fn invalid_state(msg: impl Into<String>) -> Self {
        Self::InvalidState(msg.into())
    }

    pub fn conflict(msg: impl Into<String>) -> Self {
        Self::Conflict(msg.into())
    }
}

// HTTP status code mapping (for Axum/Actix handlers)
impl DomainError {
    pub fn status_code(&self) -> u16 {
        match self {
            Self::Validation(_) => 400,
            Self::Unauthorized(_) => 403,
            Self::NotFound(_) => 404,
            Self::Conflict(_) => 409,
            Self::InvalidState(_) => 422,
            Self::Infrastructure(_) => 500,
        }
    }
}
```

---

## 規範 6：依賴注入 (Compile-time)

### 使用泛型

```rust
// Compile-time DI using generics

pub struct CreateWorkflowUseCase<R, E, A>
where
    R: WorkflowRepository,
    E: EventPublisher,
    A: AuthorizationService,
{
    repository: Arc<R>,
    event_publisher: Arc<E>,
    auth_service: Arc<A>,
}

// In main.rs or composition root
fn main() {
    let repository = Arc::new(PostgresWorkflowRepository::new(pool));
    let event_publisher = Arc::new(KafkaEventPublisher::new(config));
    let auth_service = Arc::new(AccessControlAdapter::new(client));
    
    let use_case = CreateWorkflowUseCase::new(
        repository,
        event_publisher,
        auth_service,
    );
}
```

### 使用 dyn Trait (Runtime DI)

```rust
// Runtime DI using trait objects

pub struct CreateWorkflowUseCase {
    repository: Arc<dyn WorkflowRepository>,
    event_publisher: Arc<dyn EventPublisher>,
    auth_service: Arc<dyn AuthorizationService>,
}

impl CreateWorkflowUseCase {
    pub fn new(
        repository: Arc<dyn WorkflowRepository>,
        event_publisher: Arc<dyn EventPublisher>,
        auth_service: Arc<dyn AuthorizationService>,
    ) -> Self {
        Self { repository, event_publisher, auth_service }
    }
}
```

---

## 規範 7：BDD 測試 (cucumber-rs)

```rust
// tests/acceptance/create_workflow.rs

use cucumber::{given, when, then, World};

#[derive(Debug, World)]
#[world(init = Self::new)]
pub struct CreateWorkflowWorld {
    // test state
}

#[given(expr = "a boardId {string} is provided")]
async fn given_board_id(world: &mut CreateWorkflowWorld, board_id: String) {
    world.input.board_id = board_id;
}

#[when("the user requests to create a workflow")]
async fn when_create(world: &mut CreateWorkflowWorld) {
    world.result = Some(world.use_case.execute(world.input.clone()).await);
}

#[then("the request should succeed")]
async fn then_success(world: &mut CreateWorkflowWorld) {
    assert!(world.result.as_ref().unwrap().is_ok());
}
```

---

## 框架與依賴推薦

| 用途 | Crate | 說明 |
|------|-------|------|
| Web Framework | axum / actix-web | Tokio-based async |
| ORM | sqlx / diesel | Compile-time SQL (sqlx) |
| Serialization | serde | JSON/YAML |
| Error Handling | thiserror / anyhow | Derive macros |
| Async Runtime | tokio | Multi-threaded |
| BDD Testing | cucumber | Gherkin support |
| Mocking | mockall | Trait mocking |
| UUID | uuid | v4 generation |
| DateTime | chrono | Timezone-aware |

### Cargo.toml 範例

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
axum = "0.7"
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres", "uuid", "chrono"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
thiserror = "1"
async-trait = "0.1"
tracing = "0.1"

[dev-dependencies]
cucumber = { version = "0.20", features = ["macros"] }
mockall = "0.12"
tokio-test = "0.4"
```

---

## 禁止模式

| 禁止 | 原因 | 替代方案 |
|------|------|----------|
| `unwrap()` 在生產代碼 | Panic 風險 | 使用 `?` 或 `expect()` with context |
| `clone()` 無必要 | 效能損耗 | 使用引用或 `Arc` |
| 公開 struct 欄位 | 破壞封裝 | 使用 getter 方法 |
| 可變全域變數 | Thread safety | 使用 `Arc<Mutex<T>>` |
| 同步 I/O | 阻塞 | 使用 async/await |
