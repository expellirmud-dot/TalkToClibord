def _get_tpm_usage(self):
    """Get tokens used in the last 60 seconds for TPM sliding window"""
    try:
        current_time = time.time()
        sixty_seconds_ago = current_time - 60
        
        # Initialize TPM tracking if not exists
        if not hasattr(self, '_tpm_tracker'):
            self._tpm_tracker = []
        
        # Remove entries older than 60 seconds
        self._tpm_tracker = [
            (timestamp, tokens) for timestamp, tokens in self._tpm_tracker 
            if timestamp > sixty_seconds_ago
        ]
        
        # Calculate total tokens in last 60 seconds
        tpm_used = sum(tokens for timestamp, tokens in self._tpm_tracker)
        
        return tpm_used
        
    except Exception as e:
        sys_log("TPM", f"Error calculating TPM usage: {e}")
        return 0

def _add_tpm_entry(self, tokens):
    """Add a TPM entry for tracking"""
    try:
        current_time = time.time()
        
        # Initialize TPM tracker if not exists
        if not hasattr(self, '_tpm_tracker'):
            self._tpm_tracker = []
        
        # Add new entry
        self._tpm_tracker.append((current_time, tokens))
        
        # Clean up old entries (older than 60 seconds)
        sixty_seconds_ago = current_time - 60
        self._tpm_tracker = [
            (timestamp, tokens) for timestamp, tokens in self._tpm_tracker 
            if timestamp > sixty_seconds_ago
        ]
        
    except Exception as e:
        sys_log("TPM", f"Error adding TPM entry: {e}")

def _start_tpm_ui_updater(self):
    """Start background thread to update TPM UI every 3 seconds"""
    def update_tpm_ui():
        while hasattr(self, '_tpm_updater_running') and self._tpm_updater_running:
            try:
                # Update dashboard every 3 seconds
                self._update_context_dashboard()
                time.sleep(3)
            except Exception as e:
                sys_log("TPM", f"Error in TPM UI updater: {e}")
                time.sleep(3)
    
    # Start background thread
    self._tpm_updater_running = True
    tpm_thread = threading.Thread(target=update_tpm_ui, daemon=True, name="TPM_Updater")
    tpm_thread.start()
    sys_log("TPM", "TPM UI updater started (updates every 3 seconds)")

def _stop_tpm_ui_updater(self):
    """Stop TPM UI updater thread"""
    if hasattr(self, '_tpm_updater_running'):
        self._tpm_updater_running = False
