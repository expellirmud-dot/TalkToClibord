def _process_command(self, command):
    try:
        # Task 3: Memory-Specific Compaction Trigger
        memory_usage_percentage, memory_tokens, memory_limit = self._calculate_memory_usage()
        
        if memory_tokens > 5000:
            self.set_indicator("WORKING", f"COMPACTING MEMORY ({memory_tokens:,} tokens)")
            self.append_text(f"\n[Memory {memory_tokens:,} > {memory_limit:,} limit -  Auto-compacting...]\n")
            self.context_compactor.compact_history(CHAT_HISTORY_JSON)
            self._update_context_dashboard()
            self.append_text("[Memory compaction complete]\n")
        
        # [V6.3.5] Check if code task and set effective identity
        is_code = self.is_code_task(command)
        effective_identity = "VISION" if is_code else self.active_identity
        self._save_chat_history("user", command)
        actual_model_key = get_model_for_identity(self.active_identity, self.active_thought)

        # Build context with current query
        context = self.context_builder.build_context(
            identity=effective_identity,
            user_input=command,
            attachments=self.attached_files
        )

        token_est = estimate_tokens(context)
        self.set_indicator("THINKING", f"SENDING {token_est} TOKENS")

        # DO NOT add TPM entry here - wait for successful response
        # self._add_tpm_entry(token_est)  # <-- REMOVE THIS LINE

        # Send request and get response
        response = self.ai_service.process_request(query=command, context=context, identity=effective_identity, model=actual_model_key)
        
        # ONLY add TPM entry AFTER successful response
        if response and not response.startswith("Error"):
            self._add_tpm_entry(token_est)  # <-- ADD HERE INSTEAD
            sys_log("TPM", f"Added {token_est} tokens to TPM tracker (successful request)")
        else:
            sys_log("TPM", f"Request failed - NOT adding {token_est} tokens to TPM tracker")

        return response
    except Exception as e:
        # DO NOT add TPM entry on error
        sys_log("TPM", f"Request error - NOT adding tokens to TPM tracker: {e}")
        return f"Error processing command: {e}"

def _handle_ai_response(self, response):
    """Handle AI response and update TPM if needed"""
    try:
        self.append_text(f"[{self.active_identity}] {response}\n")
        self._save_to_outbox(response)
        self._save_chat_history("model", response)

        # Parse AI commands
        results = self.engine.parse_ai_commands(response)
        
        # Log token usage (separate from TPM tracking)
        try:
            log_token_usage(self.active_identity, self._last_command_length, len(response))
        except:
            pass

        # Handle reflex commands
        if results:
            if self._reflex_count >= self.MAX_REFLEX_DEPTH:
                self.set_indicator("READY", "REFLEX LIMIT REACHED")
                self.append_text(f"\n[ SAFETY: Loop Depth {self._reflex_count} Reached]\n")
                self._reflex_count = 0
            else:
                self._reflex_count += 1
                self.set_indicator("THINKING", f"REFLEX {self._reflex_count}")
                self.root.after(100, self._process_reflex_commands, results)
        else:
            self._reflex_count = 0
            self.set_indicator("READY")
            self._update_context_dashboard()  # Update dashboard after successful completion

    except Exception as e:
        sys_log("UI", f"Error handling AI response: {e}")
        self.set_indicator("ERROR")
        self.append_text(f"\nError: {e}\n")
