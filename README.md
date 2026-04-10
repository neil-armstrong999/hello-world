# To-Do List Manager

A comprehensive desktop application for managing tasks with SQLite storage and Tkinter GUI.

## Features

### Core Functionality
- **Add Tasks**: Create new tasks with title, description, type, priority, and due date
- **Edit Tasks**: Update existing task details
- **Delete Tasks**: Remove tasks with confirmation dialog
- **Mark Complete/Incomplete**: Toggle task completion status
- **Persistent Storage**: All data stored in SQLite database

### Advanced Features
- **Browsable Calendar**: Left-side calendar with day/week/month/year views
- **Task Filtering**: Filter by status, type, and priority
- **Search**: Full-text search across titles, descriptions, and tags
- **Projects**: Organize tasks into projects with progress tracking
- **Tags**: Tag tasks for better organization
- **Recurrence**: Set up recurring tasks (daily, weekly, monthly, yearly)
- **Time Blocks**: Assign tasks to day, week, month, or year blocks
- **Export**: Export tasks to CSV or TXT format
- **Window State**: Saves window geometry and preferences

### Database Schema
The application uses SQLite with the following tables:

#### tasks
- `id`: Primary Key (Auto-increment)
- `title`: Task title (required)
- `description`: Task description (optional, supports subtasks via indentation)
- `completed`: Boolean (0/1)
- `type`: Task type (Work, Personal, Shopping, Health, Finance, Other)
- `priority`: Priority level (Low, Medium, High)
- `to_do_at`: Due date/time
- `created_at`: Creation timestamp
- `parent_id`: For subtask hierarchy
- `project_name`: Associated project
- `tags`: Comma-separated tags
- `recurrence_rule`: Recurrence pattern
- `recurrence_end_date`: When recurrence ends
- `recurrence_count`: Number of occurrences
- `time_block_type`: day/week/month/year

#### projects
- `id`: Primary Key
- `name`: Project name (unique)
- `description`: Project description
- `created_at`: Creation timestamp

#### tags
- `id`: Primary Key
- `name`: Tag name (unique)

## Requirements

- Python 3.x
- Tkinter (usually included with Python)
- SQLite3 (included with Python)

## Installation

No additional installation required! The application uses only standard library modules.

```bash
# Clone or download the repository
cd /workspace

# Run the application
python3 todo_manager.py
```

## Usage

### Starting the Application
```bash
python3 todo_manager.py
```

### Adding a Task
1. Click "Add Task" button
2. Enter title (required)
3. Add description and subtasks (use Tab for indentation)
4. Select type and priority from dropdowns
5. Set due date/time
6. Choose time block type (day/week/month/year)
7. Optionally assign to a project and add tags
8. Set recurrence if needed
9. Click "Save"

### Editing a Task
1. Select a task from the list
2. Click "Edit Task" or double-click the task
3. Modify fields as needed
4. Click "Save"

### Deleting Tasks
1. Select one or more tasks
2. Click "Delete Task"
3. Confirm deletion in the dialog

### Marking Tasks Complete
1. Select one or more tasks
2. Click "Mark Complete" to toggle completion status

### Using the Calendar
- **Navigate**: Use `<` and `>` buttons to move between months
- **Views**: Switch between day/week/month/year views
- **Select Date**: Click on a date to filter tasks
- **Task Indicators**: Days with tasks are highlighted

### Filtering and Search
- **Status Filter**: Show all/pending/completed tasks
- **Type Filter**: Filter by task type
- **Priority Filter**: Filter by priority level
- **Search**: Type in the search box to filter by keyword

### Projects
- Create projects using the "+" button in the task editor
- View project progress in the "Project Progress" section
- Tasks assigned to projects show completion percentage

### Exporting Data
- **CSV**: Export all tasks to a CSV file for spreadsheet analysis
- **TXT**: Export formatted text report with pending and completed sections

### Week Navigation
Use the week navigation controls to browse different weeks and see tasks scheduled for those periods.

## Keyboard Shortcuts

- **Tab** (in description field): Insert 4 spaces for subtask indentation
- **Double-click** (on task): Edit selected task

## Configuration

The application saves user preferences in `config.json`:
- Window geometry (size and position)
- Current week setting

## File Structure

```
/workspace/
├── todo_manager.py    # Main application file
├── tasks.db          # SQLite database (created on first run)
├── config.json       # User preferences (created on first run)
└── README.md         # This file
```

## Notes

- All data is stored locally in the SQLite database
- The database is created automatically on first run
- Window state is preserved between sessions
- Tasks can be organized hierarchically using indentation in the description field
- Recurring tasks can be set with various patterns and end conditions

## Troubleshooting

### Application won't start
- Ensure Python 3 is installed
- Check that Tkinter is available: `python3 -c "import tkinter"`

### Database errors
- Delete `tasks.db` to reset the database (this will delete all data)

### Display issues
- Try resizing the window
- Minimum window size is 1200x700 pixels
