# Commune - Render.com Deployment Guide

This guide explains how to deploy the Commune Flask social media application to Render.com with PostgreSQL database support.

## 🚀 Quick Deployment Steps

### Method 1: Using render.yaml (Recommended)

1. **Fork/Clone Repository**
   - Fork this repository to your GitHub account
   - Or upload your code to a new GitHub repository

2. **Connect to Render.com**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Configure Environment Variables**
   The following variables are automatically configured via `render.yaml`:
   - `DATABASE_URL` - Automatically set from PostgreSQL database
   - `SECRET_KEY` - Automatically generated
   - `FLASK_APP` - Set to `run.py`
   - `FLASK_ENV` - Set to `production`
   - `RENDER` - Set to `"1"` (enables production mode)

4. **Deploy**
   - Click "Apply" to start deployment
   - Render will create both the web service and PostgreSQL database
   - First deployment takes 5-10 minutes

### Method 2: Manual Setup

1. **Create PostgreSQL Database**
   - In Render dashboard, click "New" → "PostgreSQL"
   - Choose "Free" plan
   - Name it `commune-db`
   - Copy the "External Database URL" after creation

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Build Command**: `pip install -r requirements.txt && python render_start.py`
     - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT run:app`

3. **Set Environment Variables**
   In the web service settings, add:
   ```
   DATABASE_URL = [paste your PostgreSQL URL]
   SECRET_KEY = [generate a random string]
   FLASK_APP = run.py
   FLASK_ENV = production
   RENDER = 1
   ```

## 📊 Database Configuration

### Automatic Migrations
The app automatically handles database setup:
- Creates tables on first deployment
- Runs Flask-Migrate if available
- Falls back to direct table creation

### Manual Database Setup (if needed)
If automatic setup fails, you can manually run:

```bash
# In Render shell
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 🔧 Technical Details

### Database Support
- **Development**: SQLite (`site.db`)
- **Production**: PostgreSQL (via `DATABASE_URL`)
- Automatic URL conversion for SQLAlchemy 1.4+ compatibility

### Key Files for Deployment
- `render.yaml` - Render Blueprint configuration
- `Procfile` - Alternative process definition
- `render_start.py` - Production startup script
- `requirements.txt` - Python dependencies
- `config.py` - Environment-aware configuration

### Production Optimizations
- HTTPS enforcement
- Secure session cookies
- Gunicorn with eventlet workers (for SocketIO)
- Automatic database migrations

## 🌐 Features That Work on Render.com

✅ **User Authentication** - Registration, login, logout
✅ **Posts** - Create, edit, delete posts
✅ **Real-time Chat** - Public and private messaging
✅ **File Uploads** - Profile pictures
✅ **Database** - PostgreSQL with automatic migrations
✅ **HTTPS** - Automatic SSL certificates
✅ **WebRTC Video Calls** - Works with HTTPS

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error / Threading Issues**
   - **Symptom**: `RuntimeError: cannot notify on un-acquired lock`
   - **Cause**: SQLAlchemy threading conflicts with eventlet workers
   - **Solution**: Fixed with eventlet monkey patching and proper engine options
   - **Files**: Updated `config.py`, `run.py`, and `render_start.py`

2. **Database Connection Error**
   - Verify `DATABASE_URL` is set correctly
   - Check PostgreSQL database is running
   - Ensure database URL format is `postgresql://` not `postgres://`

3. **Static Files Not Loading**
   - Render serves static files automatically
   - Check file paths in templates

4. **SocketIO Connection Issues**
   - Ensure using eventlet worker: `--worker-class eventlet`
   - Check CORS settings if needed

5. **Video Calls Not Working**
   - WebRTC requires HTTPS (automatic on Render)
   - Check browser permissions for camera/microphone

### Logs and Debugging
- View logs in Render dashboard
- Enable debug mode temporarily by removing `RENDER` env var
- Check database connections in logs

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Flask secret key | `your-secret-key-here` |
| `FLASK_APP` | Flask application entry point | `run.py` |
| `FLASK_ENV` | Flask environment | `production` |
| `RENDER` | Enables production mode | `1` |

## 🔄 Updates and Maintenance

### Deploying Updates
1. Push changes to your GitHub repository
2. Render automatically rebuilds and deploys
3. Database migrations run automatically

### Scaling
- Free tier: 1 instance, 512MB RAM
- Upgrade to paid plans for more resources
- PostgreSQL free tier: 1GB storage

## 📞 Support

If deployment fails:
1. Check Render build logs
2. Verify all environment variables are set
3. Test locally first: `python run.py`
4. Check PostgreSQL database is accessible

For WebRTC video calling issues:
1. Ensure HTTPS is working (automatic on Render)
2. Test with two different browsers/devices
3. Check browser permissions

## 🎉 Success!

Once deployed, your app will be available at:
`https://your-app-name.onrender.com`

The first deployment may take 10-15 minutes as Render:
- Installs Python dependencies
- Sets up PostgreSQL database
- Runs database migrations
- Starts the application

After that, updates typically deploy in 2-3 minutes.
