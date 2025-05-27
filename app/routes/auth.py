"""
Authentication routes for admin login.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "orf"

def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful! Welcome to AL ORF Maintenance System.', 'success')
            logger.info(f"Admin user '{username}' logged in successfully")
            return redirect(url_for('views.index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
            logger.warning(f"Failed login attempt with username: {username}")
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout and clear session."""
    username = session.get('username', 'Unknown')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    logger.info(f"User '{username}' logged out")
    return redirect(url_for('auth.login')) 