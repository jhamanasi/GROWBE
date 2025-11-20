# Contributing to Growbe

<p align="center">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
  <img src="https://img.shields.io/badge/contributors-needed-orange.svg" alt="Contributors Needed">
</p>

Thank you for your interest in contributing to **Growbe**! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

### 🤝 For Everyone
- **Report bugs** by opening issues with detailed descriptions
- **Suggest features** and improvements
- **Improve documentation** and help text
- **Share Growbe** with others who might benefit
- **Provide feedback** on user experience

### 💻 For Developers
- **Fix bugs** and implement features
- **Add tests** for new functionality
- **Improve performance** and user experience
- **Enhance security** and error handling
- **Update dependencies** and maintain compatibility

## 🚀 Getting Started

### Development Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/growbe.git
   cd growbe
   ```

2. **Follow the setup instructions** in the main README.md

3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

### Development Workflow

1. **Make your changes** following the coding standards
2. **Test thoroughly** - run existing tests and add new ones
3. **Update documentation** if needed
4. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new financial calculator tool

   - Implements compound interest calculations
   - Adds comprehensive test coverage
   - Updates API documentation"
   ```
5. **Push and create a Pull Request**

## 📝 Coding Standards

### Python (Backend)

#### Style Guidelines
- **Black**: Automatic code formatting
- **isort**: Import sorting
- **Flake8**: Linting and style checking
- **MyPy**: Type checking (when possible)

#### Code Structure
```python
# Example of good Python code structure
from typing import Dict, Any, Optional
from .base_tool import BaseTool

class FinancialCalculatorTool(BaseTool):
    """Calculate financial metrics with comprehensive validation."""

    @property
    def name(self) -> str:
        return "financial_calculator"

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute financial calculation with input validation."""
        try:
            # Input validation
            principal = self._validate_positive_number(kwargs.get('principal'))
            rate = self._validate_percentage(kwargs.get('rate'))

            # Calculation logic
            result = self._calculate_compound_interest(principal, rate)

            return {
                "success": True,
                "result": result,
                "calculation_steps": [...],
                "metadata": {...}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
```

#### Key Principles
- **Type hints** for all function parameters and return values
- **Comprehensive error handling** with specific error types
- **Input validation** at function boundaries
- **Clear docstrings** explaining purpose and parameters
- **Single responsibility** - one function, one purpose

### TypeScript/React (Frontend)

#### Style Guidelines
- **ESLint**: Airbnb configuration with React rules
- **Prettier**: Automatic code formatting
- **TypeScript**: Strict type checking enabled

#### Component Structure
```typescript
// Good component structure
interface FinancialChartProps {
  data: ChartData[];
  title: string;
  type: 'bar' | 'line' | 'pie';
  className?: string;
}

export function FinancialChart({
  data,
  title,
  type,
  className = ''
}: FinancialChartProps) {
  const [isLoading, setIsLoading] = useState(false);

  // Component logic here

  return (
    <div className={`financial-chart ${className}`}>
      <h3 className="chart-title">{title}</h3>
      <ChartComponent data={data} type={type} />
    </div>
  );
}
```

#### Key Principles
- **Functional components** with TypeScript interfaces
- **Custom hooks** for reusable logic
- **Proper error boundaries** for error handling
- **Accessibility** (WCAG compliance)
- **Performance optimization** (React.memo, useMemo, useCallback)

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_conversation_flow.py -v

# Run with coverage
pytest --cov=tools --cov=services --cov-report=html
```

#### Testing Guidelines
- **Unit tests** for individual functions and methods
- **Integration tests** for API endpoints and tool interactions
- **Error case testing** - test failure scenarios
- **Mock external dependencies** (OpenAI API, database calls)

### Frontend Testing

```bash
# Run tests (when configured)
npm run test

# Run with coverage
npm run test -- --coverage
```

#### Testing Guidelines
- **Component testing** with React Testing Library
- **Integration testing** for user flows
- **Visual regression testing** for UI consistency
- **Accessibility testing** with axe-core

## 📚 Documentation

### Code Documentation

#### Python Docstrings
```python
def calculate_debt_payoff(
    principal: float,
    monthly_payment: float,
    interest_rate: float
) -> Dict[str, Any]:
    """
    Calculate debt payoff timeline and total interest.

    This function uses the standard loan amortization formula to determine
    how long it will take to pay off a debt given regular payments.

    Args:
        principal: The initial loan amount
        monthly_payment: Fixed monthly payment amount
        interest_rate: Annual interest rate as decimal (e.g., 0.05 for 5%)

    Returns:
        Dictionary containing:
        - months_to_payoff: Number of months until debt is paid
        - total_interest: Total interest paid over the life of the loan
        - total_paid: Total amount paid (principal + interest)
        - payoff_date: Estimated payoff date

    Raises:
        ValueError: If inputs are invalid (negative values, etc.)

    Example:
        >>> result = calculate_debt_payoff(10000, 300, 0.05)
        >>> print(f"Payoff in {result['months_to_payoff']} months")
        Payoff in 36 months
    """
```

#### Component Documentation
```typescript
/**
 * Interactive financial chart component with multiple visualization types.
 *
 * Features:
 * - Responsive design for all screen sizes
 * - Real-time data updates
 * - Export functionality (PNG, CSV)
 * - Accessibility compliant
 *
 * @param data - Array of data points to visualize
 * @param title - Chart title displayed above visualization
 * @param type - Chart type: 'bar', 'line', or 'pie'
 * @param className - Additional CSS classes for styling
 */
```

### README Updates

When adding new features:
1. **Update main README** with new capabilities
2. **Update API documentation** for new endpoints
3. **Add examples** in the usage section
4. **Update architecture diagrams** if needed

## 🔧 Tool Development

### Adding New Financial Tools

1. **Create the tool class** in `backend/tools/`:
   ```python
   from .base_tool import BaseTool

   class NewFinancialTool(BaseTool):
       @property
       def name(self) -> str:
           return "new_financial_tool"

       def execute(self, **kwargs) -> Dict[str, Any]:
           # Tool logic here
           return {"result": "success"}
   ```

2. **Add comprehensive tests** in `backend/tests/`

3. **Update documentation** in `backend/tools/README.md`

4. **Test integration** with the agent

### Tool Guidelines

- **Input validation**: Always validate and sanitize inputs
- **Error handling**: Return structured error responses
- **Documentation**: Clear examples and parameter descriptions
- **Performance**: Optimize for speed and memory usage
- **Security**: Never expose sensitive data in responses

## 🎨 UI/UX Contributions

### Design Principles

- **Accessibility First**: WCAG 2.1 AA compliance
- **Mobile First**: Responsive design starting with mobile
- **Financial Clarity**: Clear presentation of complex data
- **Trust Building**: Professional, reliable appearance

### Component Guidelines

- **Consistent naming**: Use descriptive, consistent naming
- **Reusable components**: Build for reusability
- **Props interface**: Well-defined TypeScript interfaces
- **Default values**: Sensible defaults for optional props
- **Error states**: Proper error handling and display

## 🔒 Security Considerations

### Backend Security
- **Input validation**: All user inputs validated and sanitized
- **SQL injection prevention**: Parameterized queries only
- **API authentication**: Secure endpoint access patterns
- **Error handling**: No sensitive information in error messages

### Frontend Security
- **XSS prevention**: Proper input sanitization
- **CSRF protection**: Secure API communication
- **Content Security Policy**: Restrictive CSP headers
- **Secure dependencies**: Regular dependency updates

## 📋 Pull Request Process

### Before Submitting

1. **Self-review** your code changes
2. **Run tests** and ensure they pass
3. **Update documentation** as needed
4. **Check formatting** and linting
5. **Test on multiple scenarios**

### PR Template

Please use this structure for pull requests:

```markdown
## Description
Brief description of the changes and why they're needed.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature)
- [ ] Documentation update
- [ ] Code refactoring

## Testing
Describe the testing performed:
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Cross-browser testing (if applicable)

## Screenshots (if applicable)
Add screenshots for UI changes.

## Additional Notes
Any additional context or considerations.
```

### Review Process

1. **Automated checks** run first (tests, linting, formatting)
2. **Code review** by maintainers
3. **Testing** in staging environment
4. **Approval** and merge

## 🆘 Getting Help

### Communication Channels
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community support
- **Email**: For security-related concerns

### Support Guidelines
- **Search existing issues** before creating new ones
- **Provide detailed information** when reporting bugs
- **Include code examples** when asking for help
- **Be respectful** and constructive in all communications

## 🎉 Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md** (future)
- **Mentioned in release notes**
- **Acknowledged in documentation**
- **Invited to join the core team** for significant contributions

## 📄 License

By contributing to Growbe, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to Growbe and helping democratize access to financial advice! 🚀
