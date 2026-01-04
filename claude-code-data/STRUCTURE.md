# Project Structure

```
claude-code-data/
├── src/
│   ├── types/                      # TypeScript type definitions
│   │   ├── base.ts                # Base types and enums
│   │   ├── messages.ts            # Message type definitions
│   │   └── index.ts               # Type exports
│   ├── utils/
│   │   ├── type-guards.ts         # Runtime type checking functions
│   │   └── type-guards.test.ts    # Type guard tests
│   ├── parser/
│   │   ├── conversation-parser.ts      # JSONL parsing functionality
│   │   ├── conversation-parser.test.ts # Parser tests
│   │   ├── conversation-analyzer.ts    # Statistics and analysis
│   │   └── conversation-analyzer.test.ts # Analyzer tests
│   └── index.ts                   # Main library exports
├── dist/                          # Built JavaScript and type definitions
├── test-data/                     # Example conversation files (gitignored)
├── docs/                          # Documentation from reverse engineering
│   ├── README.md                  # Documentation overview
│   ├── claude-code-data-storage-analysis.md
│   ├── conversation-format-specification.md
│   ├── data-models-and-schemas.md
│   └── implementation-notes.md
├── package.json                   # Package configuration
├── tsconfig.json                  # TypeScript config for development
├── tsconfig.build.json           # TypeScript config for building
├── vitest.config.ts              # Test configuration
├── .gitignore                    # Git ignore rules
└── README.md                     # Project README
```

## Key Features

- **Type-Safe**: Complete TypeScript interfaces for all Claude Code data structures
- **Parsing**: JSONL conversation file parsing with streaming support
- **Analysis**: Statistics calculation, conversation trees, cost tracking
- **Testing**: Comprehensive test suite with 34 passing tests
- **Modern**: Built with Vite, Vitest, and modern TypeScript conventions
- **Documentation**: Extensive reverse engineering documentation

## Build Outputs

The `dist/` directory contains:

- `index.js` / `index.d.ts` - Main library entry point
- `types/` - Type definitions
- `utils/` - Utility functions
- `parser/` - Core parsing and analysis functionality
