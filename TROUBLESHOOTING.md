# Troubleshooting Guide

## Common Issues and Solutions

### Backend Issues

#### 1. Port 8000 Already in Use
**Error:** `OSError: [WinError 10048] Only one usage of each socket address`

**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### 2. Module Import Errors
**Error:** `ModuleNotFoundError: No module named 'agents'`

**Solution:**
```bash
# Ensure you're in the correct directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Add parent directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

#### 3. Database Connection Issues
**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**
```bash
# Stop all running processes
# Delete database file
rm backend/timetable.db

# Reinitialize database
cd backend
python seed_data.py
```

#### 4. OR-Tools Installation Issues
**Error:** `ImportError: No module named 'ortools'`

**Solution:**
```bash
# Install OR-Tools
pip install ortools

# If that fails, try:
pip install --upgrade pip
pip install ortools --no-cache-dir

# For Windows with Python 3.11+:
pip install ortools==9.7.2996
```

### Frontend Issues

#### 1. Port 5173 Already in Use
**Error:** `Port 5173 is already in use`

**Solution:**
```powershell
# Find and kill process
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Or use different port
npm run dev -- --port 5174
```

#### 2. Node Dependencies Issues
**Error:** `Module not found` or `Cannot resolve dependency`

**Solution:**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# If still failing, clear npm cache
npm cache clean --force
npm install
```

#### 3. API Connection Issues
**Error:** `Network Error` or `Failed to fetch`

**Solution:**
1. Ensure backend is running on port 8000
2. Check proxy configuration in `vite.config.js`
3. Verify CORS settings in backend
4. Check browser console for detailed errors

#### 4. Build Issues
**Error:** `Build failed` or `Vite build errors`

**Solution:**
```bash
# Clear Vite cache
rm -rf .vite
npm run build

# If TypeScript errors:
npm install --save-dev @types/react @types/react-dom
```

### Agent System Issues

#### 1. Constraint Solver Timeout
**Error:** `Solver timeout reached`

**Solution:**
- Reduce problem size (fewer divisions/subjects)
- Increase timeout in `config/config.py`
- Simplify constraints
- Add more rooms/faculty to reduce conflicts

#### 2. Infeasible Timetable
**Error:** `No feasible solution found`

**Solution:**
1. Check data consistency:
   - Enough rooms for all classes
   - Sufficient faculty members
   - Room capacities match student counts
   - Lab subjects have lab rooms available

2. Reduce constraints:
   - Increase working hours
   - Add more timeslots
   - Reduce hours per week for subjects

#### 3. Agent Communication Errors
**Error:** `MCP connection failed`

**Solution:**
```bash
# Start MCP server separately
cd mcp_server
python server.py

# Check if WebSocket port is available
netstat -ano | findstr :8765
```

### Database Issues

#### 1. Migration Errors
**Error:** `Table already exists` or `Column doesn't exist`

**Solution:**
```bash
# Drop and recreate database
rm backend/timetable.db
cd backend
python seed_data.py
```

#### 2. Foreign Key Constraints
**Error:** `FOREIGN KEY constraint failed`

**Solution:**
- Ensure referenced records exist before creating dependent records
- Check department_id exists before creating subjects
- Verify data integrity in seed_data.py

### Performance Issues

#### 1. Slow Timetable Generation
**Symptoms:** Generation takes more than 30 seconds

**Solutions:**
- Reduce solver timeout
- Optimize constraints in OptimizationAgent
- Use fewer decision variables
- Implement heuristic pre-processing

#### 2. High Memory Usage
**Symptoms:** System becomes unresponsive

**Solutions:**
- Limit problem size
- Use more efficient data structures
- Implement garbage collection
- Monitor memory usage during optimization

### Development Issues

#### 1. Hot Reload Not Working
**Problem:** Changes not reflected in browser

**Solution:**
```bash
# Restart development server
npm run dev

# Clear browser cache
# Check file watchers limit (Linux/Mac)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
```

#### 2. CORS Errors
**Error:** `Access-Control-Allow-Origin`

**Solution:**
```python
# In backend/main.py, ensure CORS is properly configured
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Testing Issues

#### 1. Test Failures
**Error:** Tests fail with import errors

**Solution:**
```bash
# Run tests from correct directory
cd agents
python test_agents.py

# Ensure all dependencies are installed
pip install -r ../backend/requirements.txt
```

#### 2. Agent Tests Timeout
**Problem:** Tests hang or timeout

**Solution:**
- Reduce test data size
- Mock external dependencies
- Set shorter timeouts for tests
- Check for infinite loops in agent logic

## Getting Help

### Log Files
Check these locations for detailed error information:
- Backend: Console output where `python main.py` is running
- Frontend: Browser developer console (F12)
- Agent logs: Check orchestrator message_log

### Debug Mode
Enable debug mode for more detailed logging:

**Backend:**
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// Add to App.jsx
console.log('Debug info:', data);
```

### Common Commands Summary

```bash
# Full restart
cd backend && python main.py &
cd frontend && npm run dev &

# Reset database
rm backend/timetable.db && cd backend && python seed_data.py

# Test agents
cd agents && python test_agents.py

# Check ports
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

### Contact Information
For additional support:
- Check project documentation
- Review GitHub issues
- Contact development team