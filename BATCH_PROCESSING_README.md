# Batch Job Application Processing System

This system allows you to automatically apply to multiple jobs from your `software_engineer.csv` file using a sequential processing approach.

## Features

- ✅ **Sequential Processing**: Process jobs one by one to avoid overwhelming the system
- ✅ **Error Recovery**: Continue to next job if one fails
- ✅ **Status Tracking**: Automatically update CSV with application status
- ✅ **Resume Capability**: Skip already processed jobs
- ✅ **Progress Monitoring**: Real-time progress updates
- ✅ **Flexible Range**: Process specific rows or all jobs
- ✅ **User Interruption**: Gracefully handle Ctrl+C interruptions
- ✅ **Smart CSV Updates**: Prevents double updates and maintains accurate status

## Recent Fix (v2.0)

**Fixed Double CSV Update Issue**: The system now properly handles CSV updates to prevent overwriting correct statuses:

- **Before**: Success handlers would update CSV with "Applied", then main script would overwrite with "Error - Application Failed"
- **After**: Main script detects when handlers have already updated CSV and avoids double updates
- **Result**: Accurate status tracking and no more overwritten successful applications

## Usage

### 1. Check Current Status

First, check the current status of all jobs:

```bash
python check_status.py
```

This will show you:
- Total jobs in CSV
- How many have been processed
- Status breakdown (Applied, Not Available, External Redirect, etc.)
- Which jobs are unprocessed
- Next job to process

### 2. Process a Single Job

Apply to a specific job by row number:

```bash
python apply_from_csv.py 5
```

This will process row 5 in the CSV file.

### 3. Process All Jobs

Apply to all remaining jobs:

```bash
python apply_from_csv.py all
```

### 4. Process Jobs from a Specific Row

Start processing from a specific row:

```bash
python apply_from_csv.py all --start-from 10
```

This will process all jobs starting from row 10.

### 5. Process Limited Number of Jobs

Process only a certain number of jobs:

```bash
python apply_from_csv.py all --start-from 10 --max-jobs 5
```

This will process 5 jobs starting from row 10.

## Status Types

The system will automatically update the CSV with these status types:

- **Applied**: Successfully applied to the job
- **Not Available**: Job is no longer available
- **External Redirect**: Job redirects to external website
- **Error - Application Failed**: Application process failed
- **Error - Unexpected Failure**: Unexpected error occurred
- **Interrupted - User Stopped**: User interrupted the process
- **Can't Find Resume Element**: Could not find resume upload element
- **Error - Apply Button Not Found**: Apply button not found on page
- **Error - LLM Generation Failed**: Failed to generate application actions
- **Error - Max Steps Reached**: Exceeded maximum processing steps

## Error Handling

The system handles various error scenarios:

1. **Job Unavailable**: Detects when jobs are no longer available
2. **External Websites**: Detects when jobs redirect to external sites
3. **Missing Files**: Checks if resume/cover letter files exist
4. **Network Issues**: Handles timeouts and connection problems
5. **User Interruption**: Gracefully handles Ctrl+C interruptions
6. **Double Updates**: Prevents overwriting correct statuses

## CSV Structure

Your CSV should have these columns:
- `url`: Job URL
- `resume_filename`: Resume file name
- `coverletter_filename`: Cover letter file name
- `Applied`: Status (auto-added if not exists)
- `Application Date`: Date (auto-added if not exists)

## File Requirements

Make sure these files exist in `/Users/umairsaeed/Documents/ai/glue/generated/`:
- Resume files (PDF format)
- Cover letter files (PDF format)

## Example Workflow

1. **Check status**:
   ```bash
   python check_status.py
   ```

2. **Process first 10 jobs**:
   ```bash
   python apply_from_csv.py all --max-jobs 10
   ```

3. **Check progress**:
   ```bash
   python check_status.py
   ```

4. **Continue from where you left off**:
   ```bash
   python apply_from_csv.py all --start-from 11
   ```

## Safety Features

- **5-second delay** between jobs to avoid overwhelming SEEK
- **Automatic skip** of already processed jobs
- **Graceful interruption** with Ctrl+C
- **Comprehensive logging** of all actions
- **CSV backup** through automatic status updates
- **Smart status tracking** prevents double updates

## Troubleshooting

### If a job fails:
- Check the error message in the console
- The job will be marked with an appropriate error status
- The system will continue to the next job

### If you need to restart:
- Use `python check_status.py` to see where you left off
- Use `--start-from` to resume from a specific row

### If files are missing:
- Ensure resume and cover letter files exist in the generated folder
- Check file names match exactly with CSV entries

### If you see double updates:
- This issue has been fixed in v2.0
- Each job will only be updated once with the correct status

## Monitoring Progress

The system provides real-time feedback:
- Current job being processed
- Success/failure status
- Progress counters
- Final summary with statistics
- Clear indication when CSV is updated

## Best Practices

1. **Start small**: Test with a few jobs first
2. **Monitor progress**: Use `check_status.py` regularly
3. **Check files**: Ensure all resume/cover letter files exist
4. **Be patient**: 5-second delays between jobs are intentional
5. **Backup CSV**: Keep a backup of your CSV file

## Testing

To test the system with a single job:

```bash
python test_batch_fix.py
```

This will test the fix for double CSV updates.

## Commands Summary

| Command | Description |
|---------|-------------|
| `python check_status.py` | Check status of all jobs |
| `python apply_from_csv.py 5` | Process single job (row 5) |
| `python apply_from_csv.py all` | Process all remaining jobs |
| `python apply_from_csv.py all --start-from 10` | Start from row 10 |
| `python apply_from_csv.py all --max-jobs 5` | Process only 5 jobs |
| `python test_batch_fix.py` | Test the batch processing fix | 