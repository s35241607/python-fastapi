# C# .NET 後端開發規範 C# .NET Backend Standards

## 目錄 Table of Contents

1. [技術棧規範](#技術棧規範)
2. [專案結構](#專案結構)
3. [Clean Code 原則](#clean-code-原則)
4. [Code First 開發](#code-first-開發)
5. [API 開發規範](#api-開發規範)
6. [測試規範](#測試規範)
7. [效能與安全](#效能與安全)

## 技術棧規範

### 核心技術
- **.NET**: 8+
- **Web 框架**: ASP.NET Core Web API
- **ORM**: Entity Framework Core 8+
- **資料庫**: PostgreSQL with Npgsql
- **依賴注入**: 內建 DI Container
- **API 文檔**: Swagger/OpenAPI

### NuGet 套件
```xml
<PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="8.0.0" />
<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="8.0.0" />
<PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="8.0.0" />
<PackageReference Include="FluentValidation.AspNetCore" Version="11.3.0" />
<PackageReference Include="AutoMapper.Extensions.Microsoft.DependencyInjection" Version="12.0.1" />
```

## 專案結構

### Clean Architecture 結構
```
Backend.API/
├── src/
│   ├── Backend.API/              # 展示層 (Web API)
│   │   ├── Controllers/          # API 控制器
│   │   ├── Program.cs            # 應用程式入口點
│   │   └── appsettings.json      # 應用程式設定
│   ├── Backend.Application/      # 應用層
│   │   ├── Services/             # 應用服務
│   │   ├── DTOs/                 # 資料傳輸物件
│   │   └── Validators/           # 驗證器
│   ├── Backend.Domain/           # 領域層
│   │   ├── Entities/             # 領域實體
│   │   ├── ValueObjects/         # 值物件
│   │   ├── Services/             # 領域服務
│   │   └── Repositories/         # 儲存庫介面
│   └── Backend.Infrastructure/   # 基礎設施層
│       ├── Data/                 # 資料存取
│       │   ├── Contexts/         # DbContext
│       │   ├── Configurations/   # 實體配置
│       │   └── Repositories/     # 儲存庫實作
│       └── Services/             # 外部服務
└── tests/
    ├── Backend.UnitTests/        # 單元測試
    └── Backend.IntegrationTests/ # 整合測試
```

## Clean Code 原則

### 命名規範
```csharp
// 類別名稱 - PascalCase
public class UserService
{
    // 私有欄位 - camelCase with underscore prefix
    private readonly IUserRepository _userRepository;
    private readonly ILogger<UserService> _logger;

    // 屬性 - PascalCase
    public string CurrentUserName { get; set; }
    public bool IsAuthenticated { get; set; }

    // 方法名稱 - PascalCase，使用動詞開頭
    public async Task<UserDto> GetUserByIdAsync(int userId)
    {
        var userData = await _userRepository.GetByIdAsync(userId);
        return userData;
    }
}

// 介面命名 - I前綴 + PascalCase
public interface IUserRepository
{
    Task<User> GetByIdAsync(int id);
    Task<IEnumerable<User>> GetAllAsync();
}

// 常數 - PascalCase
public static class ApplicationConstants
{
    public const int MaxRetryAttempts = 3;
    public const string DefaultCulture = "en-US";
}
```

### 方法設計原則
```csharp
// 單一職責原則
public class TaxCalculator
{
    public decimal CalculateTax(decimal amount, decimal taxRate)
    {
        ValidateInputs(amount, taxRate);
        return amount * taxRate;
    }

    private static void ValidateInputs(decimal amount, decimal taxRate)
    {
        if (amount < 0)
            throw new ArgumentException("Amount cannot be negative", nameof(amount));

        if (taxRate < 0 || taxRate > 1)
            throw new ArgumentException("Tax rate must be between 0 and 1", nameof(taxRate));
    }
}

// 參數物件模式
public record OrderCalculationRequest(
    decimal BaseAmount,
    decimal TaxRate,
    decimal DiscountRate,
    decimal ShippingCost
);

public class OrderCalculator
{
    public decimal CalculateTotal(OrderCalculationRequest request)
    {
        var subtotal = request.BaseAmount - (request.BaseAmount * request.DiscountRate);
        var taxAmount = subtotal * request.TaxRate;
        return subtotal + taxAmount + request.ShippingCost;
    }
}
```

## Code First 開發

### 領域實體
```csharp
// Domain/Entities/User.cs
public class User
{
    public int Id { get; private set; }
    public string Username { get; private set; }
    public Email Email { get; private set; }
    public DateTime CreatedAt { get; private set; }
    public DateTime UpdatedAt { get; private set; }
    public bool IsActive { get; private set; }

    private User() { } // EF Core 需要

    public static User CreateNewUser(string username, Email email)
    {
        var now = DateTime.UtcNow;
        return new User
        {
            Username = username,
            Email = email,
            CreatedAt = now,
            UpdatedAt = now,
            IsActive = true
        };
    }

    public void Deactivate()
    {
        IsActive = false;
        UpdatedAt = DateTime.UtcNow;
    }
}

// Domain/ValueObjects/Email.cs
public class Email : IEquatable<Email>
{
    public string Value { get; }

    public Email(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Email cannot be empty", nameof(value));

        if (!IsValidEmail(value))
            throw new ArgumentException($"Invalid email format: {value}", nameof(value));

        Value = value.ToLowerInvariant();
    }

    private static bool IsValidEmail(string email)
    {
        var regex = new Regex(@"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$");
        return regex.IsMatch(email);
    }

    public bool Equals(Email other) => other != null && Value == other.Value;
    public override bool Equals(object obj) => Equals(obj as Email);
    public override int GetHashCode() => Value.GetHashCode();
    public static implicit operator string(Email email) => email.Value;
    public override string ToString() => Value;
}
```

### 儲存庫模式
```csharp
// Domain/Repositories/IUserRepository.cs
public interface IUserRepository
{
    Task<User> GetByIdAsync(int id);
    Task<User> GetByUsernameAsync(string username);
    Task<User> GetByEmailAsync(string email);
    Task<IEnumerable<User>> GetAllActiveAsync(int skip = 0, int take = 100);
    Task<User> AddAsync(User user);
    Task<User> UpdateAsync(User user);
    Task DeleteAsync(int id);
    Task<int> SaveChangesAsync();
}

// Infrastructure/Data/Repositories/UserRepository.cs
public class UserRepository : IUserRepository
{
    private readonly ApplicationDbContext _context;

    public UserRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<User> GetByIdAsync(int id)
    {
        return await _context.Users.FindAsync(id);
    }

    public async Task<User> GetByUsernameAsync(string username)
    {
        return await _context.Users
            .FirstOrDefaultAsync(u => u.Username == username);
    }

    public async Task<IEnumerable<User>> GetAllActiveAsync(int skip = 0, int take = 100)
    {
        return await _context.Users
            .Where(u => u.IsActive)
            .OrderBy(u => u.CreatedAt)
            .Skip(skip)
            .Take(take)
            .ToListAsync();
    }

    public async Task<User> AddAsync(User user)
    {
        var result = await _context.Users.AddAsync(user);
        return result.Entity;
    }

    public async Task<int> SaveChangesAsync()
    {
        return await _context.SaveChangesAsync();
    }
}
```

### Entity Framework 配置
```csharp
// Infrastructure/Data/Contexts/ApplicationDbContext.cs
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options) { }

    public DbSet<User> Users { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}

// Infrastructure/Data/Configurations/UserConfiguration.cs
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("Users");

        builder.HasKey(u => u.Id);
        builder.Property(u => u.Id).ValueGeneratedOnAdd();

        builder.Property(u => u.Username)
            .HasMaxLength(50)
            .IsRequired();
        builder.HasIndex(u => u.Username).IsUnique();

        // 值物件配置
        builder.OwnsOne(u => u.Email, email =>
        {
            email.Property(e => e.Value)
                .HasColumnName("email")
                .HasMaxLength(255)
                .IsRequired();
            email.HasIndex(e => e.Value).IsUnique();
        });

        builder.Property(u => u.CreatedAt)
            .HasDefaultValueSql("CURRENT_TIMESTAMP");
        builder.Property(u => u.UpdatedAt)
            .HasDefaultValueSql("CURRENT_TIMESTAMP");
        builder.Property(u => u.IsActive)
            .HasDefaultValue(true);
    }
}
```

## API 開發規範

### 控制器設計
```csharp
[ApiController]
[Route("api/v1/[controller]")]
[Produces("application/json")]
public class UsersController : ControllerBase
{
    private readonly IUserApplicationService _userApplicationService;
    private readonly ILogger<UsersController> _logger;

    public UsersController(
        IUserApplicationService userApplicationService,
        ILogger<UsersController> logger)
    {
        _userApplicationService = userApplicationService;
        _logger = logger;
    }

    /// <summary>
    /// 建立新使用者
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof(UserResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserResponseDto>> CreateUser(
        [FromBody] CreateUserRequestDto request)
    {
        try
        {
            var user = await _userApplicationService.CreateUserAsync(request);
            return CreatedAtAction(nameof(GetUser), new { id = user.Id }, user);
        }
        catch (DomainException ex)
        {
            _logger.LogWarning(ex, "Domain validation failed while creating user");
            return BadRequest(new { error = ex.Message });
        }
    }

    /// <summary>
    /// 根據 ID 取得使用者
    /// </summary>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(UserResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<UserResponseDto>> GetUser(int id)
    {
        var user = await _userApplicationService.GetUserByIdAsync(id);
        return user == null ? NotFound() : Ok(user);
    }
}
```

### 應用服務
```csharp
public interface IUserApplicationService
{
    Task<UserResponseDto> CreateUserAsync(CreateUserRequestDto request);
    Task<UserResponseDto> GetUserByIdAsync(int id);
    Task<IEnumerable<UserResponseDto>> GetUsersAsync(int skip = 0, int take = 20);
}

public class UserApplicationService : IUserApplicationService
{
    private readonly IUserRepository _userRepository;
    private readonly UserDomainService _userDomainService;
    private readonly IMapper _mapper;

    public UserApplicationService(
        IUserRepository userRepository,
        UserDomainService userDomainService,
        IMapper mapper)
    {
        _userRepository = userRepository;
        _userDomainService = userDomainService;
        _mapper = mapper;
    }

    public async Task<UserResponseDto> CreateUserAsync(CreateUserRequestDto request)
    {
        var email = new Email(request.Email);

        if (!await _userDomainService.IsUsernameAvailableAsync(request.Username))
            throw new DomainException("Username is already taken");

        if (await _userDomainService.IsEmailRegisteredAsync(email))
            throw new DomainException("Email is already registered");

        var user = User.CreateNewUser(request.Username, email);
        await _userRepository.AddAsync(user);
        await _userRepository.SaveChangesAsync();

        return _mapper.Map<UserResponseDto>(user);
    }
}
```

### DTO 與驗證
```csharp
public record CreateUserRequestDto
{
    [Required(ErrorMessage = "使用者名稱為必填")]
    [StringLength(50, MinimumLength = 3)]
    public string Username { get; init; }

    [Required(ErrorMessage = "電子郵件為必填")]
    [EmailAddress(ErrorMessage = "電子郵件格式不正確")]
    public string Email { get; init; }
}

public record UserResponseDto
{
    public int Id { get; init; }
    public string Username { get; init; }
    public string Email { get; init; }
    public DateTime CreatedAt { get; init; }
    public bool IsActive { get; init; }
}

public class CreateUserRequestValidator : AbstractValidator<CreateUserRequestDto>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Username)
            .NotEmpty().WithMessage("使用者名稱為必填")
            .Length(3, 50).WithMessage("使用者名稱長度必須介於 3-50 字元");

        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("電子郵件為必填")
            .EmailAddress().WithMessage("電子郵件格式不正確");
    }
}
```

## 測試規範

### 單元測試
```csharp
[TestFixture]
public class UserTests
{
    [Test]
    public void CreateNewUser_WithValidData_ShouldCreateUserCorrectly()
    {
        // Arrange
        var username = "john_doe";
        var email = new Email("john@example.com");

        // Act
        var user = User.CreateNewUser(username, email);

        // Assert
        user.Should().NotBeNull();
        user.Username.Should().Be(username);
        user.Email.Should().Be(email);
        user.IsActive.Should().BeTrue();
    }

    [Test]
    public void Deactivate_WhenCalled_ShouldSetIsActiveFalse()
    {
        // Arrange
        var user = User.CreateNewUser("test_user", new Email("test@example.com"));

        // Act
        user.Deactivate();

        // Assert
        user.IsActive.Should().BeFalse();
    }
}

[TestFixture]
public class UserApplicationServiceTests
{
    private Mock<IUserRepository> _mockUserRepository;
    private Mock<UserDomainService> _mockUserDomainService;
    private UserApplicationService _userApplicationService;

    [SetUp]
    public void SetUp()
    {
        _mockUserRepository = new Mock<IUserRepository>();
        _mockUserDomainService = new Mock<UserDomainService>(Mock.Of<IUserRepository>());

        _userApplicationService = new UserApplicationService(
            _mockUserRepository.Object,
            _mockUserDomainService.Object,
            Mock.Of<IMapper>());
    }

    [Test]
    public async Task CreateUserAsync_WithValidData_ShouldReturnUserDto()
    {
        // Arrange
        var request = new CreateUserRequestDto
        {
            Username = "john_doe",
            Email = "john@example.com"
        };

        _mockUserDomainService.Setup(x => x.IsUsernameAvailableAsync(request.Username))
            .ReturnsAsync(true);
        _mockUserDomainService.Setup(x => x.IsEmailRegisteredAsync(It.IsAny<Email>()))
            .ReturnsAsync(false);

        // Act
        var result = await _userApplicationService.CreateUserAsync(request);

        // Assert
        result.Should().NotBeNull();
        _mockUserRepository.Verify(x => x.AddAsync(It.IsAny<User>()), Times.Once);
    }
}
```

### 整合測試
```csharp
[TestFixture]
public class UsersControllerTests
{
    private WebApplicationFactory<Program> _factory;
    private HttpClient _client;

    [SetUp]
    public void SetUp()
    {
        _factory = new WebApplicationFactory<Program>();
        _client = _factory.CreateClient();
    }

    [Test]
    public async Task CreateUser_WithValidData_ShouldReturn201()
    {
        // Arrange
        var request = new CreateUserRequestDto
        {
            Username = "integration_test_user",
            Email = "integration@example.com"
        };

        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        // Act
        var response = await _client.PostAsync("/api/v1/users", content);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
    }
}
```

## 效能與安全

### 非同步最佳實踐
```csharp
public class UserService
{
    private readonly ApplicationDbContext _context;

    public async Task<IEnumerable<User>> GetUsersWithOrdersAsync(IEnumerable<int> userIds)
    {
        // 使用 Include 避免 N+1 查詢
        return await _context.Users
            .Include(u => u.Orders)
            .Where(u => userIds.Contains(u.Id))
            .ToListAsync();
    }

    public async Task ProcessUsersAsync(IEnumerable<int> userIds)
    {
        // 控制並發數量
        var semaphore = new SemaphoreSlim(10);
        var tasks = userIds.Select(async userId =>
        {
            await semaphore.WaitAsync();
            try
            {
                await ProcessUserAsync(userId);
            }
            finally
            {
                semaphore.Release();
            }
        });

        await Task.WhenAll(tasks);
    }
}
```

### 安全性最佳實踐
```csharp
public class SecurityService
{
    public static string SanitizeInput(string input)
    {
        if (string.IsNullOrWhiteSpace(input))
            return string.Empty;

        return input.Trim()
            .Replace("<", "&lt;")
            .Replace(">", "&gt;")
            .Replace("&", "&amp;");
    }

    public static bool IsValidPassword(string password)
    {
        if (string.IsNullOrWhiteSpace(password) || password.Length < 8)
            return false;

        var hasUpper = password.Any(char.IsUpper);
        var hasLower = password.Any(char.IsLower);
        var hasDigit = password.Any(char.IsDigit);
        var hasSpecial = password.Any(c => "!@#$%^&*(),.?\":{}|<>".Contains(c));

        return hasUpper && hasLower && hasDigit && hasSpecial;
    }
}
```

### 設定與依賴注入
```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

// 服務註冊
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<UserDomainService>();
builder.Services.AddScoped<IUserApplicationService, UserApplicationService>();

builder.Services.AddAutoMapper(typeof(Program));
builder.Services.AddFluentValidationAutoValidation();
builder.Services.AddValidatorsFromAssemblyContaining<CreateUserRequestValidator>();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// 中介軟體管線
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

---

*最後更新: 2025-01-XX*
