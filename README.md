# Core Marketing Bot

A production-ready Slack bot for streamlined marketing campaign management at Fetch Rewards.

## Features

- **Unified Campaign Workflow**: Physical events and email-only campaigns
- **Team-Specific Workflows**: Kate/Karen (events) + Jheryl (emails) 
- **AI-Powered Suggestions**: Campaign idea generation
- **Modal Navigation**: Consistent, error-resilient UI flows
- **Integration Ready**: Monday.com, Google Calendar, Google Docs/Slides

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-token"
   export SLACK_SIGNING_SECRET="your-secret"
   export OPENAI_API_KEY="your-key"
   ```

3. **Run the bot**:
   ```bash
   python main.py
   ```

4. **Use in Slack**:
   - `/help` - Opens the Fetch Campaign Hub
   - Choose campaign type and follow guided workflow

## Project Structure

```
├── main.py                 # Application entry point
├── handlers/              # Slack event handlers
│   ├── core_slash_commands.py
│   ├── simple_handlers.py
│   └── core_clean_actions.py
├── modals/               # Modal UI definitions
│   └── core_modal_system.py
├── services/             # External integrations
│   ├── ai_service.py
│   ├── monday_service.py
│   └── google_*.py
├── utils/               # Utility functions
│   └── slack_formatting.py
└── config/              # Configuration
    ├── config.py
    └── requirements.txt
```

## Workflows

### Physical Event Campaign
- **Assignees**: Kate/Karen (event planning) + Jheryl (email marketing)
- **Tasks**: 5 event tasks + 6 email tasks
- **Calendar**: Reminders for event deadlines

### Email-Only Campaign  
- **Assignee**: Jheryl
- **Tasks**: 6 email workflow tasks
- **Calendar**: No reminders (per request)

## Architecture

- **Async/Await**: High-performance async handlers
- **Modal System**: Standardized navigation with fallbacks
- **Caching Strategy**: Static modals cached, dynamic fresh
- **Error Handling**: Robust fallback mechanisms

## Contributing

1. Follow existing code patterns
2. Use standardized modal navigation
3. Test both workflow types
4. Maintain separation of concerns

## Production Notes

- All handlers use centralized `handle_modal_navigation`
- Caching optimized for performance vs freshness
- Comprehensive error handling and logging
- Team-specific workflow validation

Built for the Fetch Rewards marketing team with ❤️