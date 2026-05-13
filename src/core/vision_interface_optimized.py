def _update_context_dashboard(self):
        """[V6.3.5] Optimized Context Dashboard with Reduced Logging"""
        try:
            # 1. Get model-specific token limit
            model_key = get_model_for_identity(self.active_identity, self.active_thought)
            max_limit = MODELS_CONFIG.get(model_key, {}).get("max_input_tokens", 12000)
            self.context_dashboard.max_tokens = max_limit
            
            # 2. Get current query from input box
            try:
                current_query = self.input_box.get("1.0", tk.END).strip()
            except Exception as e:
                current_query = ""
            
            # 3. Check if we need to rebuild context (avoid unnecessary builds)
            # Only rebuild if query changed or attachments changed
            query_hash = hash(current_query + str(sorted(self.attached_files)))
            
            if hasattr(self, '_last_context_hash') and self._last_context_hash == query_hash:
                # Use cached values - no need to rebuild
                if hasattr(self, '_cached_context_data'):
                    self._update_ui_from_cache()
                    return
            
            # 4. Build actual context only when needed
            try:
                actual_context = self.context_builder.build_context(
                    identity=self.active_identity,
                    user_input=current_query,
                    attachments=self.attached_files
                )
            except Exception as e:
                actual_context = ""
            
            # 5. Calculate real tokens from actual context
            total_tokens = 0
            system_tokens = 0
            memory_tokens = 0
            file_tokens = 0
            query_tokens = 0
            
            if actual_context:
                total_tokens = estimate_tokens(actual_context)
                
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
            
            # 6. Cache the results
            self._last_context_hash = query_hash
            self._cached_context_data = {
                'total_tokens': total_tokens,
                'system_tokens': system_tokens,
                'memory_tokens': memory_tokens,
                'file_tokens': file_tokens,
                'query_tokens': query_tokens,
                'model_key': model_key,
                'max_limit': max_limit
            }
            
            # 7. Update dashboard
            self._update_dashboard_with_data()
            
        except Exception as e:
            # Reduce error logging frequency
            if not hasattr(self, '_last_dashboard_error_time') or \
               time.time() - self._last_dashboard_error_time > 30:  # Log error only once per 30 seconds
                sys_log("DASHBOARD", f"Dashboard update error: {e}")
                self._last_dashboard_error_time = time.time()

    def _update_ui_from_cache(self):
        """Update UI from cached data to avoid unnecessary context building"""
        try:
            if hasattr(self, '_cached_context_data'):
                data = self._cached_context_data
                
                # Update dashboard with cached values
                self.context_dashboard.set_system_instruction_tokens(int(data['system_tokens']))
                self.context_dashboard.set_memory_tokens(int(data['memory_tokens']))
                self.context_dashboard.set_file_data_tokens(int(data['file_tokens']))
                self.context_dashboard.set_user_query_tokens(int(data['query_tokens']))
                
                # Get TPM data
                tpm_used = self._get_tpm_usage()
                
                # Calculate percentages
                payload_usage_percentage = (data['total_tokens'] / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
                tpm_percentage = (tpm_used / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
                
                # Format UI
                health_bar = self.context_dashboard.format_for_ui(style="health_bar", usage_percentage=payload_usage_percentage)
                
                token_text = f"{data['model_key'].upper()} | Payload: {data['total_tokens']:,}/{data['max_limit']:,} TK"
                token_text += f" | TPM: {tpm_used:,}/{data['max_limit']:,}"
                
                # Add warnings
                if payload_usage_percentage >= 90:
                    token_text += " | Payload High"
                elif tpm_percentage >= 90:
                    token_text += " | TPM High"
                
                # Update UI
                def refresh_labels():
                    try:
                        self.context_dashboard_label.config(text=health_bar)
                        self.token_lbl.config(text=token_text)
                    except Exception: pass
                
                self.root.after(0, refresh_labels)
                
        except Exception as e:
            sys_log("DASHBOARD", f"Cache update error: {e}")

    def _update_dashboard_with_data(self):
        """Update dashboard with current data"""
        try:
            if not hasattr(self, '_cached_context_data'):
                return
            
            data = self._cached_context_data
            
            # Update dashboard
            self.context_dashboard.set_system_instruction_tokens(int(data['system_tokens']))
            self.context_dashboard.set_memory_tokens(int(data['memory_tokens']))
            self.context_dashboard.set_file_data_tokens(int(data['file_tokens']))
            self.context_dashboard.set_user_query_tokens(int(data['query_tokens']))
            
            # Get TPM data
            tpm_used = self._get_tpm_usage()
            
            # Calculate percentages
            payload_usage_percentage = (data['total_tokens'] / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
            
            # Format UI
            health_bar = self.context_dashboard.format_for_ui(style="health_bar", usage_percentage=payload_usage_percentage)
            
            token_text = f"{data['model_key'].upper()} | Payload: {data['total_tokens']:,}/{data['max_limit']:,} TK"
            token_text += f" | TPM: {tpm_used:,}/{data['max_limit']:,}"
            
            # Add warnings
            if payload_usage_percentage >= 90:
                token_text += " | Payload High"
            elif tpm_percentage >= 90:
                token_text += " | TPM High"
            
            # Log only when significant changes occur
            if not hasattr(self, '_last_logged_tokens') or \
               abs(data['total_tokens'] - self._last_logged_tokens) > 100:  # Log only when tokens change by >100
                sys_log("DASHBOARD", f"Updated: {data['total_tokens']} tokens ({payload_usage_percentage:.1f}%)")
                self._last_logged_tokens = data['total_tokens']
            
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
        """Start optimized TPM UI updater with reduced frequency"""
        def update_tpm_ui():
            while hasattr(self, '_tpm_updater_running') and self._tpm_updater_running:
                try:
                    # Update dashboard but with reduced context building
                    self._update_context_dashboard()
                    time.sleep(3)  # Keep 3-second interval but optimize the update process
                except Exception as e:
                    sys_log("TPM", f"Error in TPM UI updater: {e}")
                    time.sleep(3)
        
        # Start background thread
        self._tpm_updater_running = True
        tpm_thread = threading.Thread(target=update_tpm_ui, daemon=True, name="TPM_Updater")
        tpm_thread.start()
        sys_log("TPM", "Optimized TPM UI updater started")
