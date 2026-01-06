# Clinical Report Query Generator

AI-powered clinical data analysis platform that combines traditional SQL-based data extraction with advanced LLM-based analysis capabilities.

## 🎯 Overview

**Clinical Report Query Generator** is a Streamlit-based application that enables pharmaceutical researchers and clinical data analysts to generate SQL queries and insights from natural language requests. The system leverages Google's Gemini AI models for intelligent query generation and provides real-time execution on Databricks.

### Key Features

- **🏥 Disease Pipeline**: Disease-centric analysis with 4 core + 7 AI-recommended recipes
- **💬 NL2SQL**: Natural language to SQL conversion with RAG pattern and real-time execution
- **📊 Schema Chatbot**: Interactive Q&A assistant for database schema understanding
- **📈 Auto Chart Recommendation**: Smart data visualization based on result patterns
- **⭐ Query History**: Persistent storage with favorites and reuse functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API Key
- Databricks SQL Warehouse Access (optional, for query execution)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd clinical_report_generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API credentials:
```bash
# Copy and edit config.yaml
cp config.yaml.example config.yaml
# Add your Gemini API key and Databricks credentials
```

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## 📁 Project Structure

```
clinical_report_generator/
├── app.py                      # Main Streamlit application
├── ARCHITECTURE.md             # Detailed system architecture
├── README.md                   # This file
│
├── features/                   # UI Components (3 Streamlit tabs)
│   ├── disease_pipeline_tab.py
│   ├── nl2sql_tab.py
│   └── schema_chatbot_tab.py
│
├── pipelines/                  # Business Logic Orchestration
│   ├── disease_pipeline.py
│   └── nl2sql_generator.py
│
├── components/                 # Reusable UI Components
│   └── chart_builder.py
│
├── core/                       # Domain Logic
│   ├── recipe_loader.py
│   └── sql_template_engine.py
│
├── services/                   # External APIs
│   ├── gemini_service.py
│   ├── databricks_client.py
│   ├── schema_chatbot.py
│   └── parameter_extractor.py
│
├── utils/                      # Pure Utilities
│   ├── parsers.py
│   ├── formatters.py
│   ├── visualization.py
│   ├── session_state.py
│   ├── query_history.py
│   └── chart_recommender.py
│
├── prompts/                    # LLM Prompt Templates
│   ├── shared/
│   ├── report_generation/
│   ├── recipe_recommendation/
│   └── nl2sql/
│
├── recipes/                    # SQL Recipe Templates (42 recipes)
│   ├── pool/                   # 10 patient pool recipes
│   └── profile/                # 32 patient profile recipes
│
├── tests/                      # Test Suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── reports/                # Test result reports
│
├── docs/                       # Documentation
│   ├── DEVLOG.md              # Development history
│   ├── CLAUDE_GUIDE.md        # AI assistant guide
│   ├── DATABRICKS_SETUP.md
│   ├── implementation/         # Implementation guides
│   ├── archive/                # Deprecated files
│   └── sql_debug/              # Debug SQL queries
│
└── tools/                      # Development tools
    └── generate_all_sql.py
```

## 🔧 Configuration

### config.yaml

```yaml
api_keys:
  gemini_api_key: "YOUR_GEMINI_API_KEY"

databricks:
  server_hostname: "adb-xxx.azuredatabricks.net"
  http_path: "/sql/1.0/warehouses/xxx"
  access_token: "dapiXXXXXXXX"
```

Alternatively, use environment variables:
```bash
export DATABRICKS_SERVER_HOSTNAME="adb-xxx.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/xxx"
export DATABRICKS_TOKEN="dapiXXXXXXXX"
```

## 📖 Usage

### Tab 1: Disease Pipeline

1. Enter a disease keyword (e.g., "고혈압", "당뇨병")
2. System executes 4 core recipes automatically
3. AI recommends 7 additional recipes based on disease characteristics
4. Review and select desired recipes
5. Optionally refine with natural language feedback
6. Execute approved recipes and view results

### Tab 2: NL2SQL

1. Enter natural language query (e.g., "고혈압 환자의 성별 분포")
2. Click "🚀 SQL 생성" to generate SQL
3. Review generated SQL and quality metrics
4. Click "▶️ 쿼리 실행" to execute on Databricks
5. View results with auto-recommended charts
6. Save to favorites for reuse

### Tab 3: Schema Chatbot

1. Ask questions about database schema
2. System retrieves relevant tables/columns using RAG
3. AI provides detailed explanations and examples
4. Maintains conversation history for follow-up questions

## 🎨 Features in Detail

### Auto Chart Recommendation (Phase 18)

The system automatically analyzes query results and recommends optimal chart types:
- **1 column**: Histogram or bar/pie chart
- **2 columns**: Categorical+numeric → pie/bar, numeric+numeric → scatter
- **3+ columns**: Bar chart with optional color grouping

**8 Chart Types**: Bar, Line, Scatter, Line+Scatter, Pie, Area, Box, Histogram

**7 Color Palettes**: Clinical, Nature, Science, Colorblind-friendly, Blue Gradient, Professional, Default

### Query History & Favorites (Phase 19)

- **Auto-save**: Every generated query is automatically saved
- **Favorites**: Star frequently used queries
- **Reuse**: One-click copy to input field
- **Statistics**: Track success rates and execution times
- **Export**: Export selected queries to SQL file

### Production Stability Features (Phase 16)

- **Safe Date Parsing**: Uses `TRY_TO_DATE()` to handle invalid dates
- **User-Friendly Errors**: Categorized error messages with troubleshooting steps
- **Comprehensive Logging**: Daily log files with query performance tracking

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/unit/
```

### Run Integration Tests
```bash
python -m pytest tests/integration/
```

### Run All Tests
```bash
python -m pytest tests/
```

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed system architecture and design decisions
- **[docs/DEVLOG.md](./docs/DEVLOG.md)** - Complete development history (Phase 1-19)
- **[docs/CLAUDE_GUIDE.md](./docs/CLAUDE_GUIDE.md)** - Comprehensive guide for AI assistants
- **[docs/DATABRICKS_SETUP.md](./docs/DATABRICKS_SETUP.md)** - Databricks configuration guide

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: Google Gemini 2.5-Flash
- **Database**: Databricks (Spark SQL)
- **Visualization**: Plotly
- **Template Engine**: Jinja2
- **Data Processing**: Pandas

## 📊 System Metrics

- **42 SQL Recipes**: Pre-built templates for common analyses
- **96% Execution Success Rate**: Phase 15 test results
- **100% SQL Generation Success**: With RAG-enhanced schema understanding
- **8 Chart Types**: Professional data visualization options
- **7 Color Palettes**: Including colorblind-friendly options

## 🔐 Security Features

- **Privacy Masking**: Automatic masking of personal data (name, phone, SSN)
- **SQL Injection Prevention**: Parameterized queries and validation
- **Access Control**: Databricks token-based authentication

## 🐛 Known Issues & Limitations

See [docs/DEVLOG.md](./docs/DEVLOG.md) "Technical Debt" section for:
- Duplicate SQL rendering logic
- Missing automated tests for some modules
- Config management improvements needed
- Type hints consistency

## 🚧 Roadmap

### Planned Improvements
1. **Automated Testing**: Comprehensive pytest test suite for all layers
2. **Type Hints**: Full mypy compliance
3. **Config Management**: Unified configuration module with validation
4. **Code Consolidation**: Eliminate duplicate SQL rendering logic
5. **Monitoring Dashboard**: Visualize query success rates and performance

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

[Add license information]

## 👥 Authors

[Add author information]

## 🙏 Acknowledgments

- Google Gemini API for LLM capabilities
- Databricks for SQL Warehouse infrastructure
- Streamlit for rapid UI development

---

**Last Updated**: 2025-10-19 (Project reorganization completed)
**Version**: Phase 19 (Query History & Favorites)
