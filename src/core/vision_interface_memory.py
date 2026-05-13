def _calculate_memory_usage(self):
    """Calculate memory usage percentage from chat_history.json only"""
    try:
        # Read chat history file
        if os.path.exists(CHAT_HISTORY_JSON):
            with open(CHAT_HISTORY_JSON, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # Calculate tokens from history data
            if isinstance(history_data, list):
                history_text = "\n".join(str(entry) for entry in history_data)
            else:
                history_text = json.dumps(history_data, ensure_ascii=False)
            
            memory_tokens = estimate_tokens(history_text)
            
            # Set memory limit (adjustable - default 5000)
            memory_limit = 5000
            
            # Calculate usage percentage
            memory_usage_percentage = (memory_tokens / memory_limit) * 100 if memory_limit > 0 else 0
            
            return memory_usage_percentage, memory_tokens, memory_limit
        else:
            return 0, 0, 5000
            
    except Exception as e:
        sys_log("MEMORY", f"Error calculating memory usage: {e}")
        return 0, 0, 5000

def _process_command(self, command):
    try:
        # Task 3: Memory-Specific Compaction Trigger
        # DO NOT use total_context_percentage
        # INSTEAD, calculate only the tokens in chat_history.json
        memory_usage_percentage, memory_tokens, memory_limit = self._calculate_memory_usage()
        
        # If memory_tokens > 5000 (adjustable limit), trigger compaction
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

        # Add TPM entry for tracking
        self._add_tpm_entry(token_est)

        return self.ai_service.process_request(query=command, context=context, identity=effective_identity, model=actual_model_key)
    except Exception as e:
        return f"Error processing command: {e}"
