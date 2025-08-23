# Development Guidelines

## Code Standards

### Python (Backend) Standards

#### Code Formatting and Style
- **Code Formatter**: Black with 88-character line length
- **Linter**: flake8 for code quality and style
- **Type Checking**: mypy for static type analysis
- **Import Sorting**: isort for consistent import organization
- **Testing Framework**: pytest with pytest-asyncio for async tests

#### Formatting Commands
```bash
# Format code
uv run black app/

# Check code quality
uv run flake8 app/

# Type checking
uv run mypy app/

# Sort imports
uv run isort app/

# Run tests
uv run pytest
```

#### Python Code Structure
```python
"""Module docstring explaining the purpose of the module."""

from typing import Optional, List
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas import UserCreate, UserResponse


class UserService:
    """Service class for user-related operations."""
    
    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user response
            
        Raises:
            HTTPException: If user creation fails
        """
        # Implementation here
        pass
```

### TypeScript/JavaScript (Frontend) Standards

#### Code Formatting and Style
- **Code Formatter**: Prettier
- **Linter**: ESLint with Vue and TypeScript integration
- **Type Checking**: vue-tsc for Vue Single File Components
- **Style Guide**: Vue ESLint configuration

#### Formatting Commands
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check

# Run tests (if configured)
npm run test
```

#### Vue Component Structure
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { User } from '@/types'

// Props
interface Props {
  userId?: string
}
const props = withDefaults(defineProps<Props>(), {
  userId: ''
})

// Composables
const router = useRouter()

// Reactive state
const users = ref<User[]>([])
const loading = ref(false)

// Computed properties
const filteredUsers = computed(() => {
  return users.value.filter(user => user.active)
})

// Methods
const fetchUsers = async (): Promise<void> => {
  loading.value = true
  try {
    // API call implementation
  } catch (error) {
    console.error('Error fetching users:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="user-component">
    <h1>Users</h1>
    <div v-if="loading" class="loading">
      Loading...
    </div>
    <div v-else>
      <div
        v-for="user in filteredUsers"
        :key="user.id"
        class="user-item"
      >
        {{ user.name }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-component {
  padding: 1rem;
}

.loading {
  text-align: center;
  color: #666;
}

.user-item {
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
}
</style>
```

### Naming Conventions

#### Backend Naming Conventions
- **Files**: snake_case (e.g., `user_repository.py`)
- **Classes**: PascalCase (e.g., `UserRepository`)
- **Functions/Methods**: snake_case (e.g., `get_user_by_id`)
- **Variables**: snake_case (e.g., `user_data`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DATABASE_URL`)
- **Private methods**: Leading underscore (e.g., `_validate_user`)
- **Protected methods**: Single leading underscore (e.g., `_process_data`)

#### Frontend Naming Conventions
- **Files**: kebab-case for components (e.g., `user-list.vue`)
- **Classes**: PascalCase (e.g., `UserService`)
- **Functions/Methods**: camelCase (e.g., `getUserById`)
- **Variables**: camelCase (e.g., `userData`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)
- **Vue Components**: PascalCase (e.g., `UserList`)
- **Props**: camelCase (e.g., `userId`)

## Git Workflow

### Branch Strategy

#### Branch Types
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **bugfix/**: Bug fix branches
- **hotfix/**: Critical production fixes
- **release/**: Release preparation branches

#### Branch Naming Conventions
- **Feature**: `feature/description` (e.g., `feature/user-authentication`)
- **Bugfix**: `bugfix/description` (e.g., `bugfix/login-error`)
- **Hotfix**: `hotfix/description` (e.g., `hotfix/security-patch`)
- **Release**: `release/version` (e.g., `release/v1.2.0`)

### Commit Message Format

#### Standard Format
```
type(scope): brief description

Detailed explanation of the change (optional)

- List of changes (optional)
- Breaking changes (if any)

Closes #issue-number
```

#### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes

#### Examples
```bash
# Feature commit
feat(auth): add JWT token authentication

- Implement JWT token generation and validation
- Add middleware for protected routes
- Update user model with authentication fields

Closes #123

# Bug fix commit
fix(api): resolve user creation validation error

The email validation was not properly checking for duplicate emails
in the database, causing 500 errors on user registration.

Closes #456

# Breaking change commit
feat(api)!: update user schema structure

BREAKING CHANGE: User schema now requires 'email' field and removes 'username' field.
Migration script provided in scripts/migrate_user_schema.py

Closes #789
```

### Pull Request Process

#### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented where necessary
- [ ] Documentation updated
- [ ] No new warnings or errors

## Screenshots (if applicable)
Add screenshots to show the change

## Related Issues
Closes #issue-number
```

## Code Review Guidelines

### Review Checklist

#### Functionality
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Performance considerations addressed

#### Code Quality
- [ ] Code is readable and maintainable
- [ ] Follows established patterns
- [ ] No code duplication
- [ ] Appropriate abstractions used

#### Testing
- [ ] Adequate test coverage
- [ ] Tests are meaningful
- [ ] Tests follow naming conventions
- [ ] Edge cases tested

#### Security
- [ ] No sensitive data exposed
- [ ] Input validation implemented
- [ ] SQL injection prevention
- [ ] Authentication/authorization correct

### Review Process
1. **Self Review**: Author reviews their own code first
2. **Automated Checks**: CI/CD pipeline runs all tests and checks
3. **Peer Review**: At least one team member reviews the code
4. **Address Feedback**: Author addresses all review comments
5. **Final Approval**: Reviewer approves the changes
6. **Merge**: Code is merged to target branch

## Testing Standards

### Backend Testing

#### Test Structure
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user():
    """Test user creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/users",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123"
            }
        )
    
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

#### Test Categories
- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test component interactions
- **API Tests**: Test API endpoints
- **Database Tests**: Test database operations

### Frontend Testing

#### Test Structure
```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UserList from '@/components/UserList.vue'

describe('UserList', () => {
  it('renders user list correctly', () => {
    const wrapper = mount(UserList, {
      props: {
        users: [
          { id: 1, name: 'John Doe', email: 'john@example.com' }
        ]
      }
    })
    
    expect(wrapper.text()).toContain('John Doe')
    expect(wrapper.find('.user-item').exists()).toBe(true)
  })
})
```

## Documentation Standards

### Code Documentation

#### Python Docstrings
```python
def calculate_total(items: List[Item], tax_rate: float = 0.1) -> float:
    """Calculate total price including tax.
    
    Args:
        items: List of items to calculate total for
        tax_rate: Tax rate to apply (default: 0.1 for 10%)
        
    Returns:
        Total price including tax
        
    Raises:
        ValueError: If tax_rate is negative
        
    Example:
        >>> items = [Item(price=10), Item(price=20)]
        >>> calculate_total(items, 0.05)
        31.5
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

#### TypeScript Documentation
```typescript
/**
 * Fetches user data from the API
 * @param userId - The ID of the user to fetch
 * @param includeInactive - Whether to include inactive users
 * @returns Promise that resolves to user data
 * @throws {Error} When user is not found
 * 
 * @example
 * ```typescript
 * const user = await fetchUser('123', false)
 * console.log(user.name)
 * ```
 */
async function fetchUser(
  userId: string, 
  includeInactive: boolean = false
): Promise<User> {
  // Implementation
}
```

### API Documentation

#### FastAPI Endpoint Documentation
```python
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session)
) -> UserResponse:
    """
    Create a new user.
    
    - **email**: User's email address (must be unique)
    - **username**: User's username (must be unique)
    - **password**: User's password (will be hashed)
    
    Returns the created user data without the password.
    """
    # Implementation
```

## Security Guidelines

### Backend Security
- Always validate and sanitize input data
- Use parameterized queries to prevent SQL injection
- Hash passwords using bcrypt
- Implement proper authentication and authorization
- Use HTTPS in production
- Keep dependencies updated
- Log security events

### Frontend Security
- Validate all user inputs
- Sanitize data before displaying
- Use HTTPS for all API calls
- Store sensitive data securely
- Implement proper error handling
- Avoid exposing sensitive information in client-side code

## Performance Guidelines

### Backend Performance
- Use async/await for I/O operations
- Implement database connection pooling
- Add appropriate database indexes
- Use caching for frequently accessed data
- Optimize database queries
- Monitor API response times

### Frontend Performance
- Use lazy loading for components
- Implement virtual scrolling for large lists
- Optimize images and assets
- Use code splitting
- Implement proper caching strategies
- Monitor bundle sizes

## Deployment Guidelines

### Environment Configuration
- Use environment variables for configuration
- Never commit secrets to version control
- Use different configurations for different environments
- Implement proper logging levels
- Use health checks for monitoring

### Docker Best Practices
- Use multi-stage builds
- Minimize image layers
- Use specific version tags
- Implement proper security scanning
- Use non-root users in containers