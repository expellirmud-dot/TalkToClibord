# vision_expense_tracker.py (V2.0 - Advanced Token Expense Tracking)
import os
import csv
import time
import threading
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from collections import defaultdict
from vision_config import MODELS_CONFIG

class ExpenseTracker:
    """Advanced expense tracking with in-memory caching and budget management"""
    
    def __init__(self, logs_dir="data/logs"):
        self.logs_dir = logs_dir
        self._in_memory_expenses = []
        self._session_expenses = defaultdict(list)
        self._identity_expenses = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'count': 0})
        self._flush_interval = 60  # Flush every 60 seconds
        self._last_flush = time.time()
        self._lock = threading.Lock()
        
        # Budget limits
        self.daily_budget = 100.0  # THB per day
        self.monthly_budget = 3000.0  # THB per month
        self.minute_budget = 10.0  # THB per minute
        
        # Rate limiting
        self._minute_expenses = []
        self._rate_limit_enabled = True
        
        # Start background flush thread
        self._flush_thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self._flush_thread.start()
        
        print(f"[Expense] ExpenseTracker V2.0 initialized")
    
    def log_token_usage(self, model_id, in_tk, out_tk, identity=None, session_id=None):
        """Log token usage with in-memory tracking"""
        try:
            # Get price info
            price_info = next((v for k, v in MODELS_CONFIG.items() if v['id'] == model_id), MODELS_CONFIG['jamie'])
            cost = (in_tk * price_info['in_price']) + (out_tk * price_info['out_price'])
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Create expense record
            expense_record = {
                'timestamp': datetime.now(),
                'model_id': model_id,
                'in_tokens': in_tk,
                'out_tokens': out_tk,
                'cost': cost,
                'identity': identity,
                'session_id': session_id
            }
            
            with self._lock:
                # 🔧 Check for duplicates (same session_id, model, and tokens within 1 second)
                is_duplicate = False
                for existing in self._in_memory_expenses:
                    time_diff = abs((expense_record['timestamp'] - existing['timestamp']).total_seconds())
                    if (existing['session_id'] == session_id and 
                        existing['model_id'] == model_id and
                        existing['in_tokens'] == in_tk and
                        existing['out_tokens'] == out_tk and
                        time_diff < 1.0):
                        is_duplicate = True
                        print(f"[Expense] Duplicate record detected for session {session_id}, skipping")
                        break
                
                if not is_duplicate:
                    # Add to in-memory cache
                    self._in_memory_expenses.append(expense_record)
                    
                    # Add to session tracking
                    if session_id:
                        self._session_expenses[session_id].append(expense_record)
                    
                    # Add to identity tracking
                    if identity:
                        self._identity_expenses[identity]['cost'] += cost
                        self._identity_expenses[identity]['tokens'] += (in_tk + out_tk)
                        self._identity_expenses[identity]['count'] += 1
                    
                    # Add to rate limiting tracking
                    if self._rate_limit_enabled:
                        self._minute_expenses.append(expense_record)
                        # Clean up old expenses (older than 1 minute)
                        self._minute_expenses = [
                            e for e in self._minute_expenses 
                            if datetime.now() - e['timestamp'] < timedelta(minutes=1)
                        ]
            
            # Check budget limits
            self._check_budget_limits(cost, identity)
            
            # Check rate limits
            self._check_rate_limits(cost)
            
            return cost, session_id
            
        except Exception as e:
            print(f"[Expense] Error logging token usage: {e}")
            return 0.0, None
    
    def _periodic_flush(self):
        """Background thread to periodically flush expenses to CSV"""
        while True:
            time.sleep(self._flush_interval)
            try:
                self.flush_to_csv()
            except Exception as e:
                print(f"[Expense] Flush error: {e}")
    
    def flush_to_csv(self):
        """Flush in-memory expenses to CSV file"""
        with self._lock:
            if not self._in_memory_expenses:
                return
            
            try:
                if not os.path.exists(self.logs_dir):
                    os.makedirs(self.logs_dir)
                
                expense_file = os.path.join(self.logs_dir, "expense_log.csv")
                file_exists = os.path.exists(expense_file)
                
                with open(expense_file, "a", encoding="utf-8", newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header if needed
                    if not file_exists or os.path.getsize(expense_file) == 0:
                        writer.writerow([
                            "Timestamp", "Model", "Input", "Output", "Cost_THB", 
                            "Identity", "Session_ID"
                        ])
                    
                    # Write all in-memory expenses
                    for record in self._in_memory_expenses:
                        writer.writerow([
                            record['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                            record['model_id'],
                            record['in_tokens'],
                            record['out_tokens'],
                            f"{record['cost']:.6f}",
                            record.get('identity', ''),
                            record.get('session_id', '')
                        ])
                
                print(f"[Expense] Flushed {len(self._in_memory_expenses)} records to CSV")
                self._in_memory_expenses.clear()
                self._last_flush = time.time()
                
            except Exception as e:
                print(f"[Expense] CSV flush error: {e}")
    
    def _check_budget_limits(self, cost, identity):
        """Check if expense exceeds budget limits"""
        try:
            daily_expense = self.get_daily_expense()
            monthly_expense = self.get_monthly_expense()
            
            # Daily budget check
            if daily_expense + cost > self.daily_budget:
                remaining = self.daily_budget - daily_expense
                print(f"[Expense] BUDGET ALERT: Daily budget exceeded! Remaining: {remaining:.2f} THB")
            
            # Monthly budget check
            if monthly_expense + cost > self.monthly_budget:
                remaining = self.monthly_budget - monthly_expense
                print(f"[Expense] BUDGET ALERT: Monthly budget exceeded! Remaining: {remaining:.2f} THB")
            
        except Exception as e:
            print(f"[Expense] Budget check error: {e}")
    
    def _check_rate_limits(self, cost):
        """Check if expense exceeds rate limits"""
        try:
            if not self._rate_limit_enabled:
                return
            
            minute_expense = sum(e['cost'] for e in self._minute_expenses) + cost
            
            if minute_expense > self.minute_budget:
                print(f"[Expense] RATE LIMIT ALERT: Minute budget exceeded! Current: {minute_expense:.2f} THB")
                
        except Exception as e:
            print(f"[Expense] Rate limit check error: {e}")
    
    def predict_cost(self, text, model_id, identity=None):
        """Predict cost for a given text and model"""
        try:
            # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
            estimated_tokens = len(text) // 4
            
            # Get price info
            price_info = next((v for k, v in MODELS_CONFIG.items() if v['id'] == model_id), MODELS_CONFIG['jamie'])
            
            # Assume 50% input, 50% output
            estimated_cost = (estimated_tokens * 0.5 * price_info['in_price']) + \
                           (estimated_tokens * 0.5 * price_info['out_price'])
            
            # Add margin for safety
            estimated_cost *= 1.5
            
            return estimated_cost, estimated_tokens
            
        except Exception as e:
            print(f"[Expense] Cost prediction error: {e}")
            return 0.0, 0
    
    @lru_cache(maxsize=128)
    def get_daily_expense(self, date=None):
        """Get daily expense with caching"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            expense_file = os.path.join(self.logs_dir, "expense_log.csv")
            if not os.path.exists(expense_file):
                return 0.0
            
            with open(expense_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                daily_total = sum(
                    float(row['Cost_THB'])
                    for row in reader
                    if row['Timestamp'].startswith(date)
                )
            
            # Add in-memory expenses
            with self._lock:
                in_memory_daily = sum(
                    e['cost'] for e in self._in_memory_expenses
                    if e['timestamp'].strftime("%Y-%m-%d") == date
                )
            
            return daily_total + in_memory_daily
            
        except Exception as e:
            print(f"[Expense] Daily expense error: {e}")
            return 0.0
    
    @lru_cache(maxsize=12)
    def get_monthly_expense(self, year=None, month=None):
        """Get monthly expense with caching"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        try:
            expense_file = os.path.join(self.logs_dir, "expense_log.csv")
            if not os.path.exists(expense_file):
                return 0.0
            
            month_str = f"{year:04d}-{month:02d}"
            
            with open(expense_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                monthly_total = sum(
                    float(row['Cost_THB'])
                    for row in reader
                    if row['Timestamp'].startswith(month_str)
                )
            
            # Add in-memory expenses
            with self._lock:
                in_memory_monthly = sum(
                    e['cost'] for e in self._in_memory_expenses
                    if e['timestamp'].strftime("%Y-%m") == month_str
                )
            
            return monthly_total + in_memory_monthly
            
        except Exception as e:
            print(f"[Expense] Monthly expense error: {e}")
            return 0.0
    
    def get_total_expense(self):
        """Get total expense from CSV and in-memory records"""
        try:
            expense_file = os.path.join(self.logs_dir, "expense_log.csv")
            if not os.path.exists(expense_file):
                return 0.0
            
            with open(expense_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_total = sum(float(row['Cost_THB']) for row in reader)
            
            # Add in-memory expenses
            with self._lock:
                in_memory_total = sum(e['cost'] for e in self._in_memory_expenses)
            
            return csv_total + in_memory_total
            
        except Exception as e:
            print(f"[Expense] Total expense error: {e}")
            return 0.0
    
    def get_identity_breakdown(self):
        """Get expense breakdown by identity"""
        with self._lock:
            return dict(self._identity_expenses)
    
    def get_session_expenses(self, session_id):
        """Get expenses for a specific session"""
        with self._lock:
            return self._session_expenses.get(session_id, [])
    
    def get_real_time_stats(self):
        """Get real-time expense statistics"""
        with self._lock:
            total_in_memory = sum(e['cost'] for e in self._in_memory_expenses)
            minute_expense = sum(e['cost'] for e in self._minute_expenses)
            
            return {
                'in_memory_records': len(self._in_memory_expenses),
                'in_memory_cost': total_in_memory,
                'minute_expense': minute_expense,
                'daily_expense': self.get_daily_expense(),
                'monthly_expense': self.get_monthly_expense(),
                'identity_breakdown': dict(self._identity_expenses),
                'active_sessions': len(self._session_expenses),
                'last_flush': self._last_flush
            }
    
    def set_budget_limits(self, daily=None, monthly=None, minute=None):
        """Set budget limits"""
        if daily is not None:
            self.daily_budget = daily
        if monthly is not None:
            self.monthly_budget = monthly
        if minute is not None:
            self.minute_budget = minute
        
        print(f"[Expense] Budget limits updated: Daily={self.daily_budget}, Monthly={self.monthly_budget}, Minute={self.minute_budget}")
    
    def enable_rate_limiting(self, enabled=True):
        """Enable or disable rate limiting"""
        self._rate_limit_enabled = enabled
        print(f"[Expense] Rate limiting {'enabled' if enabled else 'disabled'}")
