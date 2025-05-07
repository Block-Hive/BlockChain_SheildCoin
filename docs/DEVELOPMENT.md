# Development Guide

This guide provides information for developers who want to contribute to the BlockChain project. It covers the development environment setup, code organization, testing procedures, and contribution guidelines.

## Development Environment

### Setting Up Your Development Environment

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/blockchain.git
cd blockchain
```

2. **Create a virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Set up the database**:

```bash
# Install PostgreSQL if not already installed
# For example, on Ubuntu:
# sudo apt-get install postgresql postgresql-contrib

# Create a database for development
createdb blockchain_dev

# Set environment variables
export BLOCKCHAIN_DB_NAME=blockchain_dev
export BLOCKCHAIN_DB_USER=your_username
export BLOCKCHAIN_DB_PASSWORD=your_password

# Initialize the database
python -m blockchain.utils.initializer
```

5. **Run the development server**:

```bash
python -m blockchain.api.app --host 127.0.0.1 --port 5000
```

### Development Tools

We recommend using the following tools for development:

- **IDE**: VS Code or PyCharm with Python extensions
- **Linter**: flake8
- **Code Formatter**: black
- **Type Checker**: mypy
- **Test Runner**: pytest

## Code Organization

The codebase is organized into the following main directories:

```
blockchain/
├── api/              # RESTful API implementation
│   ├── app.py        # Flask application entry point
│   ├── routes/       # API route definitions
│   └── models/       # API request/response models
├── core/             # Core blockchain implementation
│   ├── blockchain.py # Main blockchain class
│   ├── block.py      # Block implementation
│   └── transaction.py# Transaction implementation
├── crypto/           # Cryptographic utilities
│   └── wallet.py     # Wallet implementation
├── network/          # P2P networking
│   ├── node.py       # Node implementation
│   └── dht.py        # DHT implementation
├── utils/            # Utility functions and classes
│   ├── database.py   # Database interface
│   ├── storage.py    # Storage management
│   └── initializer.py# System initialization
├── config.py         # Configuration settings
└── main.py           # Command-line interface
```

## Coding Standards

### Python Style Guide

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide with a few modifications:

- Maximum line length is 100 characters
- Use 4 spaces for indentation
- Use double quotes for strings unless single quotes avoid backslashes

### Type Annotations

All new code should include type annotations following [PEP 484](https://www.python.org/dev/peps/pep-0484/):

```python
def add_transaction(self, transaction: Transaction) -> bool:
    """
    Add a transaction to the transaction pool.
    
    Args:
        transaction: The transaction to add
        
    Returns:
        True if the transaction was added successfully, False otherwise
    """
    # Implementation
```

### Documentation

All modules, classes, and methods should have docstrings following the [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

```python
def mine_block(self, difficulty: int) -> None:
    """
    Mine the block by finding a hash with the specified number of leading zeros.
    
    The mining process involves incrementing the nonce value until a hash
    is found that meets the difficulty criteria.
    
    Args:
        difficulty: The number of leading zeros required in the hash
        
    Raises:
        ValueError: If the difficulty is less than 1
    """
    # Implementation
```

## Testing

### Test Structure

Tests are organized in a parallel structure to the main codebase:

```
tests/
├── api/              # API tests
├── core/             # Core blockchain tests
├── crypto/           # Cryptography tests
├── network/          # Network tests
├── utils/            # Utility tests
└── conftest.py       # Pytest configuration and fixtures
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/core/test_blockchain.py

# Run with coverage report
pytest --cov=blockchain

# Generate HTML coverage report
pytest --cov=blockchain --cov-report=html
```

### Test Guidelines

1. **Unit Tests**: Every module should have corresponding unit tests
2. **Integration Tests**: Critical interactions between components should have integration tests
3. **Mocking**: Use mocks for external dependencies (database, network, etc.)
4. **Test Coverage**: Aim for at least 80% test coverage for new code
5. **Test Documentation**: Include docstrings in test functions explaining what is being tested

Example test:

```python
def test_add_valid_transaction():
    """Test that a valid transaction is correctly added to the transaction pool."""
    # Arrange
    wallet = Wallet()
    recipient = "recipient_address"
    transaction = Transaction(wallet.get_address(), recipient, 10.0)
    wallet.sign_transaction(transaction)
    pool = TransactionPool()
    
    # Act
    result = pool.add_transaction(transaction)
    
    # Assert
    assert result is True
    assert len(pool.get_transactions()) == 1
    assert pool.get_transactions()[0].signature == transaction.signature
```

## Pull Request Workflow

1. **Fork the Repository**: Create your own fork of the repository
2. **Create a Branch**: Create a feature branch from the main branch
3. **Develop Your Feature**: Make your changes, following the coding standards
4. **Write Tests**: Add tests for your new feature or bug fix
5. **Run the Test Suite**: Ensure all tests pass
6. **Update Documentation**: Update relevant documentation
7. **Create a Pull Request**: Submit a PR with a clear description of the changes

### PR Guidelines

- Keep PRs focused on a single feature or bug fix
- Include a clear description of what the PR does
- Reference any related issues
- Include screenshots or examples if relevant
- Ensure all CI checks pass

## Continuous Integration

We use GitHub Actions for continuous integration. The CI pipeline includes:

1. **Linting**: flake8 and black checks
2. **Type Checking**: mypy static type analysis
3. **Testing**: Running the test suite with pytest
4. **Coverage**: Ensuring adequate test coverage

## Development Workflow

### Feature Development

1. **Create an Issue**: Describe the feature you want to implement
2. **Discuss the Implementation**: Get feedback on your approach
3. **Implement the Feature**: Follow the coding standards and write tests
4. **Submit a PR**: Follow the PR workflow described above

### Bug Fixes

1. **Create an Issue**: Describe the bug with steps to reproduce
2. **Diagnose the Issue**: Identify the root cause
3. **Implement a Fix**: Make the necessary changes and add tests
4. **Submit a PR**: Follow the PR workflow described above

## Performance Considerations

When developing for the blockchain, keep these performance considerations in mind:

1. **Database Access**: Minimize database queries and use efficient query patterns
2. **Cryptographic Operations**: Be aware of the performance impact of crypto operations
3. **Network Communication**: Optimize serialization and minimize network overhead
4. **Memory Usage**: Be mindful of memory usage, especially for large blockchains
5. **Mining Performance**: Optimize the mining algorithm for efficiency

## Security Best Practices

Security is critical for blockchain applications. Follow these best practices:

1. **Input Validation**: Validate all user inputs
2. **Cryptographic Best Practices**: Use secure cryptographic algorithms and libraries
3. **Secrets Management**: Never commit secrets to version control
4. **Authentication**: Implement proper authentication for sensitive operations
5. **Rate Limiting**: Protect against DoS attacks with rate limiting
6. **Error Handling**: Do not expose sensitive information in error messages

## Documentation

### Updating Documentation

When making changes that affect the user-facing behavior or API:

1. Update the relevant documentation files in the `docs/` directory
2. Update docstrings in the code
3. If applicable, update example code

### Building Documentation

We use MkDocs for building documentation:

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Release Process

1. **Version Bump**: Update version number in `setup.py` and `blockchain/__init__.py`
2. **Changelog**: Update the CHANGELOG.md file with the new changes
3. **Release Branch**: Create a release branch (e.g., `release/1.2.0`)
4. **Tag the Release**: Tag the release in git (`git tag v1.2.0`)
5. **Release Notes**: Create release notes in GitHub
6. **PyPI Release**: Publish the package to PyPI

## Troubleshooting

### Common Development Issues

1. **Database Connection Issues**:
   - Check that PostgreSQL is running
   - Verify database credentials are correct
   - Ensure the database exists

2. **Test Failures**:
   - Ensure your development environment is properly set up
   - Check for recent changes that might have affected tests
   - Verify that you have the latest dependencies

3. **API Issues**:
   - Check the API logs for error messages
   - Verify that the API server is running on the expected host/port
   - Ensure your requests are properly formatted

## Community

Join our development community:

- **Discord**: [Join our Discord server](https://discord.gg/blockchain)
- **Mailing List**: Subscribe to our [developer mailing list](mailto:blockchain-dev@example.com)
- **Issues**: Discuss features and bugs on our [GitHub Issues](https://github.com/yourusername/blockchain/issues)

## Resources

- [Python Documentation](https://docs.python.org/3/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Blockchain Concepts](https://en.wikipedia.org/wiki/Blockchain)
- [Cryptography in Python](https://cryptography.io/en/latest/) 