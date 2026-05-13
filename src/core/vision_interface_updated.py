def _update_context_dashboard(self):
        """[V6.3.5] Real-time Payload Preview with Time-based Rate Limit Calculation"""
        try:
            # 1. Get model-specific token limit
            model_key = get_model_for_identity(self.active_identity, self.active_thought)
            max_limit = MODELS_CONFIG.get(model_key, {}).get("max_input_tokens", 12000)
            self.context_dashboard.max_tokens = max_limit
            
            # 2. Get current query from input box for real-time preview
            try:
                current_query = self.input_box.get("1.0", tk.END).strip()
            except Exception as e:
                sys_log("DASHBOARD", f"Error getting current query: {e}")
                current_query = ""
            
            # 3. Build EXACT context that would be sent right now
            try:
                actual_context = self.context_builder.build_context(
                    identity=self.active_identity,
                    user_input=current_query,  # Use actual current query
                    attachments=self.attached_files
                )
            except Exception as e:
                sys_log("DASHBOARD", f"Error building actual context: {e}")
                actual_context = ""
            
            # 4. Calculate real tokens from actual context
            total_tokens = 0
            system_tokens = 0
            memory_tokens = 0
            file_tokens = 0
            query_tokens = 0
            
            if actual_context:
                # Calculate total tokens first
                total_tokens = estimate_tokens(actual_context)
                
                # Parse context into sections for detailed breakdown
                sections = actual_context.split("\n\n")
                
                for section in sections:
                    if section.startswith("[SYSTEM]"):
                        system_tokens = estimate_tokens(section)
                    elif section.startswith("[MEMORY]"):
                        memory_tokens = estimate_tokens(section)
                    elif section.startswith("[FILES]"):
                        file_tokens = estimate_tokens(section)
                    elif section.startswith("[USER]"):
                        query_tokens = estimate_tokens(section)
            
            # 5. Update file token cache for future use
            for f in self.attached_files:
                f_str = str(f)
                if f_str not in self.file_token_cache and os.path.exists(f_str):
                    try:
                        with open(f_str, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                            self.file_token_cache[f_str] = estimate_tokens(content)
                    except Exception as e:
                        sys_log("ATTACHMENT", f"Error caching file {f_str}: {e}")
            
            # 6. Update Model with actual payload tokens
            self.context_dashboard.set_system_instruction_tokens(int(system_tokens))
            self.context_dashboard.set_memory_tokens(int(memory_tokens))
            self.context_dashboard.set_file_data_tokens(int(file_tokens))
            self.context_dashboard.set_user_query_tokens(int(query_tokens))
            
            # 7. Calculate payload usage percentage
            payload_usage_percentage = (total_tokens / max_limit) * 100 if max_limit > 0 else 0
            
            # 8. Get TPM sliding window data
            tpm_used = self._get_tpm_usage()
            tpm_percentage = (tpm_used / max_limit) * 100 if max_limit > 0 else 0
            
            # 9. Format UI with both payload and TPM info
            health_bar = self.context_dashboard.format_for_ui(style="health_bar", usage_percentage=payload_usage_percentage)
            
            # Show both payload and TPM information
            token_text = f"{model_key.upper()} | Payload: {total_tokens:,} / {max_limit:,} TK | TPM: {tpm_used:,} / {max_limit:,}"
            
            # Add warnings
            if payload_usage_percentage >= 90:
                token_text += " | Payload High"
            elif tpm_percentage >= 90:
                token_text += " | TPM High"
            
            # 4. Update UI safely on Main Thread
            def refresh_labels():
                try:
                    self.context_dashboard_label.config(text=health_bar)
                    self.token_lbl.config(text=token_text)
                except Exception: pass
                
            self.root.after(0, refresh_labels)

        except Exception as e:
            sys_log("DASHBOARD", f"Dashboard update error: {e}")
