# BRAIN Project - Modular Structure

This document describes the modular structure implemented for the BRAIN Expression Template Decoder application.

## Overview

The application has been refactored to use Flask blueprints for better code organization and maintainability. The application is divided into several functional modules including paper analysis, feature engineering, idea generation, and inspiration.

## Project Structure

```
BRAINProject/
├── 运行打开我.py                   # Main Flask application entry point
├── blueprints/                     # Blueprint modules
│   ├── __init__.py                # Package initialization
│   ├── feature_engineering.py     # Feature engineering blueprint
│   ├── idea_house.py              # Idea house blueprint (Coze integration)
│   ├── inspiration_house.py       # Inspiration house blueprint
│   └── paper_analysis.py          # Paper analysis blueprint
├── templates/
│   ├── index.html                 # Main page template
│   ├── feature_engineering.html   # Feature engineering page template
│   ├── idea_house.html            # Idea house page template
│   ├── inspiration_house.html     # Inspiration house page template
│   └── paper_analysis.html        # Paper analysis page template
├── static/
│   ├── script.js                  # Main application JavaScript
│   ├── feature_engineering.js     # Feature engineering JavaScript
│   ├── idea_house.js              # Idea house JavaScript
│   ├── inspiration_house.js       # Inspiration house JavaScript
│   ├── paper_analysis.js          # Paper analysis JavaScript
│   ├── brain.js                   # BRAIN API functions
│   ├── decoder.js                 # Template decoder functions
│   └── styles.css                 # Application styles
└── requirements.txt               # Python dependencies
```

## Blueprint Structure

### Paper Analysis Blueprint (`blueprints/paper_analysis.py`)
Handles paper analysis functionality.
- Routes: `/paper-analysis/`
- Features: File processing (PDF, DOCX, etc.), Deepseek API integration.

### Feature Engineering Blueprint (`blueprints/feature_engineering.py`)
Handles feature engineering tasks.
- Routes: `/feature-engineering/`
- Features: Deepseek/Kimi API integration for feature generation.

### Idea House Blueprint (`blueprints/idea_house.py`)
Handles idea generation using Coze API.
- Routes: `/idea-house/`
- Features: Coze API integration for processing data fields.

### Inspiration House Blueprint (`blueprints/inspiration_house.py`)
Handles inspiration generation.
- Routes: `/inspiration-house/`
- Features: Deepseek/Kimi API integration.

### Main Application (`运行打开我.py`)
The main application entry point.
- Routes: Main application routes, BRAIN API authentication.
- Features: Auto-dependency installation, Blueprint registration.

## Benefits of This Structure

1. **Modularity**: Related functionality is grouped together in blueprints
2. **Maintainability**: Easier to maintain and update individual modules
3. **Scalability**: Easy to add new blueprints for additional features
4. **Separation of Concerns**: Each blueprint handles a specific domain
5. **Testability**: Individual modules can be tested independently


## Dependencies

### Main Application Dependencies:
- Flask
- Flask-CORS
- requests
- pandas (for BRAIN API integration)

### Module Specific Dependencies:
- **Paper Analysis**: PyPDF2, pdfplumber, python-docx, docx2txt, striprtf, PyMuPDF
- **Idea House**: cozepy (for Coze API)

## Adding New Blueprints

To add a new blueprint:

1. Create a new file in the `blueprints/` directory
2. Define your blueprint:
   ```python
   from flask import Blueprint
   
   new_blueprint = Blueprint('new_feature', __name__, url_prefix='/new-feature')
   
   @new_blueprint.route('/')
   def index():
       return render_template('new_feature.html')
   ```
3. Import and register the blueprint in the main application file (`运行打开我.py`):
   ```python
   from blueprints.new_feature import new_blueprint
   app.register_blueprint(new_blueprint)
   ```

## Notes

- The paper analysis JavaScript file (`static/paper_analysis.js`) has been updated to use the new blueprint URLs
- The main index template has been updated to link to the correct blueprint route
- Unused imports have been removed from the main application file
- All paper analysis functionality remains intact but is now properly modularized 