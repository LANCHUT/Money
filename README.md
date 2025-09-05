# Money Management Application

A PyQt6-based financial management application with a clean, organized structure.

## Project Structure

```
Money/
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── build_release.py           # Build script
├── Money.iss                  # Inno Setup installer script
│
├── models/                    # Data models and business logic
│   ├── __init__.py
│   ├── account.py            # Account model
│   ├── operation.py          # Operation model
│   ├── position.py           # Position model
│   ├── placement.py          # Placement models
│   ├── tier.py               # Tier models
│   ├── category.py           # Category models
│   ├── beneficiary.py        # Beneficiary models
│   ├── payment_method.py     # Payment method model
│   ├── loan.py               # Loan model
│   ├── echeance.py           # Echeance model
│   └── enums.py              # Enumerations
│
├── views/                     # User interface components
│   ├── __init__.py
│   ├── dialogs/              # Dialog windows
│   │   ├── __init__.py
│   │   ├── BaseDialog.py     # Base dialog class
│   │   ├── AddEdit*.py       # Add/Edit dialogs
│   │   ├── Replace*.py       # Replace dialogs
│   │   ├── Show*.py          # Show dialogs
│   │   └── ImportDialog.py   # Import dialog
│   └── ui/                   # Qt Designer UI files
│       ├── __init__.py
│       ├── MainWindow.ui
│       └── PopUp*.ui
│
├── controllers/               # Application controllers
│   ├── __init__.py
│   └── main_controller.py    # Main application controller
│
├── database/                  # Database management
│   ├── __init__.py
│   └── gestion_bd.py         # Database operations
│
├── utils/                     # Utility functions and helpers
│   ├── __init__.py
│   ├── CheckableComboBox.py  # Custom combo box
│   ├── DateTableWidgetItem.py # Date widget
│   ├── ImportQIF.py          # QIF import utility
│   ├── ComputeLoan.py        # Loan computation
│   ├── GetPlacementValue.py  # Placement value utility
│   ├── HTMLJSTemplate.py     # HTML/JS templates
│   └── WebEngineWrapper.py   # Web engine wrapper
│
├── assets/                    # Static assets
│   ├── icons/
│   │   └── Money.ico         # Application icon
│   └── sounds/
│       ├── transaction.mp3   # Sound effects
│       └── transaction.wav
│
└── config/                    # Configuration files
    └── __init__.py
```

## Key Improvements

### 1. **Organized Structure**
- **Models**: All data models are now in separate files for better maintainability
- **Views**: UI components are organized into dialogs and UI files
- **Controllers**: Main application logic is separated from UI
- **Database**: Database operations are isolated in their own module
- **Utils**: Utility functions are grouped together
- **Assets**: Static files are properly organized

### 2. **Better Separation of Concerns**
- Models handle data and business logic
- Views handle user interface
- Controllers manage application flow
- Database module handles all data persistence
- Utils provide reusable functionality

### 3. **Improved Maintainability**
- Each model is in its own file for easier maintenance
- Clear import structure with proper package organization
- Consistent naming conventions
- Better code organization

### 4. **Enhanced Readability**
- Clear directory structure makes it easy to find files
- Logical grouping of related functionality
- Proper Python package structure with `__init__.py` files

## Running the Application

```bash
python main.py
```

## Dependencies

See `requirements.txt` for the complete list of Python dependencies.

## Development

The application follows a clean architecture pattern with:
- **Models**: Data structures and business logic
- **Views**: User interface components
- **Controllers**: Application logic and coordination
- **Database**: Data persistence layer
- **Utils**: Shared utilities and helpers

This structure makes the codebase more maintainable, testable, and easier to understand for new developers.
