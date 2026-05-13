def _update_tpm_quota(self):
    """Update available TPM quota (not usage tracking)"""
    try:
        current_time = time.time()
        
        # Initialize TPM quota system if not exists
        if not hasattr(self, '_tpm_quota'):
            self._tpm_quota = 0
            self._max_tpm_quota = 16000  # Default limit
            self._last_refill_time = current_time
        
        # Calculate time passed since last refill
        time_passed = current_time - self._last_refill_time
        
        # Calculate refill amount (16,000 tokens per 60 seconds = 267 per second)
        refill_rate = 267  # tokens per second
        refill_amount = int(time_passed * refill_rate)
        
        # Refill quota (but don't exceed max)
        if refill_amount > 0:
            self._tpm_quota = min(self._tpm_quota + refill_amount, self._max_tpm_quota)
            self._last_refill_time = current_time
            
            # Log only significant refills
            if refill_amount >= 100:
                sys_log("TPM", f"Quota refilled: +{refill_amount} tokens (available: {self._tpm_quota:,})")
        
        return self._tpm_quota
        
    except Exception as e:
        sys_log("TPM", f"Error updating TPM quota: {e}")
        return 0

def _consume_tpm_quota(self, tokens):
    """Consume TPM quota when request is successful"""
    try:
        if hasattr(self, '_tpm_quota') and self._tpm_quota >= tokens:
            self._tpm_quota -= tokens
            sys_log("TPM", f"Quota consumed: -{tokens} tokens (remaining: {self._tpm_quota:,})")
            return True
        else:
            sys_log("TPM", f"Insufficient quota: need {tokens}, have {self._tpm_quota}")
            return False
            
    except Exception as e:
        sys_log("TPM", f"Error consuming TPM quota: {e}")
        return False

def _process_command(self, command):
    try:
        # ... build context and estimate tokens ...
        token_est = estimate_tokens(context)
        
        # Check if we have enough TPM quota before sending
        available_quota = self._update_tpm_quota()
        
        if available_quota < token_est:
            self.append_text(f"[TPM] Insufficient quota: need {token_est}, have {available_quota}\n")
            self.append_text("[TPM] Waiting for quota refill...\n")
            return "Please wait - insufficient TPM quota"
        
        # Send request
        response = self.ai_service.process_request(...)
        
        # Consume quota only if successful
        if response and not response.startswith("Error"):
            self._consume_tpm_quota(token_est)
            return response
        else:
            # Don't consume quota on failure
            return response
            
    except Exception as e:
        return f"Error processing command: {e}"

def _update_context_dashboard(self):
    """Update dashboard with TPM quota (not usage)"""
    try:
        # ... context building ...
        
        # Update TPM quota
        available_quota = self._update_tpm_quota()
        max_quota = self._max_tpm_quota
        
        # Calculate available percentage
        available_percentage = (available_quota / max_quota) * 100 if max_quota > 0 else 0
        
        # Format UI with quota information
        token_text = f"{model_key.upper()} | Payload: {total_tokens:,}/{max_limit:,} TK"
        token_text += f" | TPM Available: {available_quota:,}/{max_quota:,} ({available_percentage:.1f}%)"
        
        # Add warnings
        if available_quota < token_est * 2:  # Less than 2 requests worth
            token_text += " | Low Quota"
        elif available_quota < token_est:  # Not enough for this request
            token_text += " | Insufficient Quota"
        
        # Update UI
        def refresh_labels():
            try:
                self.context_dashboard_label.config(text=health_bar)
                self.token_lbl.config(text=token_text)
            except Exception: pass
        
        self.root.after(0, refresh_labels)
        
    except Exception as e:
        sys_log("DASHBOARD", f"Dashboard update error: {e}")

def _start_tpm_ui_updater(self):
    """Start TPM quota updater (every 3 seconds for smooth refill display)"""
    def update_tpm_ui():
        while hasattr(self, '_tpm_updater_running') and self._tpm_updater_running:
            try:
                # Update quota and UI every 3 seconds
                self._update_context_dashboard()
                time.sleep(3)
            except Exception as e:
                sys_log("TPM", f"Error in TPM UI updater: {e}")
                time.sleep(3)
    
    # Start background thread
    self._tpm_updater_running = True
    tpm_thread = threading.Thread(target=update_tpm_ui, daemon=True, name="TPM_Quota_Updater")
    tpm_thread.start()
    sys_log("TPM", "TPM quota updater started (refill tracking)")
