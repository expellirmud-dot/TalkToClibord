def _simulate_file_tokens(self, file_path):
    """Simulate token calculation for file attachment preview"""
    try:
        if not os.path.exists(file_path):
            return 0, "File not found"
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Quick estimation based on file type and size
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Different estimation strategies for different file types
        if file_ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c']:
            # Code files: ~4 chars per token
            estimated_tokens = file_size // 4
            file_type = "Code"
        elif file_ext in ['.txt', '.md', '.json', '.yaml', '.yml']:
            # Text files: ~4 chars per token
            estimated_tokens = file_size // 4
            file_type = "Text"
        elif file_ext in ['.html', '.css', '.xml']:
            # Markup files: ~4 chars per token
            estimated_tokens = file_size // 4
            file_type = "Markup"
        elif file_ext in ['.csv']:
            # CSV files: ~4 chars per token
            estimated_tokens = file_size // 4
            file_type = "CSV"
        else:
            # Binary files: estimate based on size
            if file_size < 1024:  # < 1KB
                estimated_tokens = 50
                file_type = "Small Binary"
            elif file_size < 10240:  # < 10KB
                estimated_tokens = 200
                file_type = "Medium Binary"
            else:
                estimated_tokens = 500
                file_type = "Large Binary"
        
        # Cap at reasonable maximum
        estimated_tokens = min(estimated_tokens, 1000)
        
        return estimated_tokens, file_type
        
    except Exception as e:
        return 0, f"Error: {e}"

def _update_file_attachment_preview(self):
    """Update file attachment preview with token estimates"""
    try:
        if not self.attached_files:
            return
        
        # Calculate total file tokens
        total_file_tokens = 0
        file_details = []
        
        for file_path in self.attached_files:
            tokens, file_type = self._simulate_file_tokens(file_path)
            total_file_tokens += tokens
            
            # Get file name for display
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            file_details.append({
                'name': file_name,
                'path': file_path,
                'tokens': tokens,
                'type': file_type,
                'size': file_size
            })
        
        # Update file token cache
        for detail in file_details:
            self.file_token_cache[detail['path']] = detail['tokens']
        
        # Show preview in UI
        if file_details:
            preview_text = f"\n[FILE PREVIEW] {len(file_details)} files attached:\n"
            for detail in file_details:
                size_str = self._format_file_size(detail['size'])
                preview_text += f"  - {detail['name']} ({detail['type']}, {size_str}) ~{detail['tokens']} tokens\n"
            preview_text += f"  [TOTAL FILE TOKENS: {total_file_tokens:,}]\n"
            
            # Update UI (if not already showing)
            if not hasattr(self, '_last_file_preview') or self._last_file_preview != preview_text:
                self.append_text(preview_text)
                self._last_file_preview = preview_text
        
        return total_file_tokens, file_details
        
    except Exception as e:
        sys_log("FILE_PREVIEW", f"Error updating file preview: {e}")
        return 0, []

def _format_file_size(self, size_bytes):
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def _update_context_dashboard_with_file_preview(self):
    """Enhanced context dashboard with file preview"""
    try:
        # 1. Get model-specific token limit
        model_key = get_model_for_identity(self.active_identity, self.active_thought)
        max_limit = MODELS_CONFIG.get(model_key, {}).get("max_input_tokens", 12000)
        self.context_dashboard.max_tokens = max_limit
        
        # 2. Get current query from input box
        try:
            current_query = self.input_box.get("1.0", tk.END).strip()
        except Exception as e:
            sys_log("DASHBOARD", f"Error getting current query: {e}")
            current_query = ""
        
        # 3. Update file attachment preview
        total_file_tokens, file_details = self._update_file_attachment_preview()
        
        # 4. Build actual context
        try:
            actual_context = self.context_builder.build_context(
                identity=self.active_identity,
                user_input=current_query,
                attachments=self.attached_files
            )
        except Exception as e:
            sys_log("DASHBOARD", f"Error building actual context: {e}")
            actual_context = ""
        
        # 5. Calculate real tokens
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
        
        # 6. Update dashboard
        self.context_dashboard.set_system_instruction_tokens(int(system_tokens))
        self.context_dashboard.set_memory_tokens(int(memory_tokens))
        self.context_dashboard.set_file_data_tokens(int(file_tokens))
        self.context_dashboard.set_user_query_tokens(int(query_tokens))
        
        # 7. Calculate percentages
        payload_usage_percentage = (total_tokens / max_limit) * 100 if max_limit > 0 else 0
        tpm_used = self._get_tpm_usage()
        tpm_percentage = (tpm_used / max_limit) * 100 if max_limit > 0 else 0
        
        # 8. Format enhanced UI
        health_bar = self.context_dashboard.format_for_ui(style="health_bar", usage_percentage=payload_usage_percentage)
        
        # Enhanced token text with file breakdown
        token_text = f"{model_key.upper()} | Payload: {total_tokens:,}/{max_limit:,} TK"
        token_text += f" | Sys:{system_tokens} Mem:{memory_tokens} Files:{file_tokens} Query:{query_tokens}"
        token_text += f" | TPM: {tpm_used:,}/{max_limit:,}"
        
        # Add warnings
        if payload_usage_percentage >= 90:
            token_text += " | Payload High"
        elif tpm_percentage >= 90:
            token_text += " | TPM High"
        
        # 9. Update UI
        def refresh_labels():
            try:
                self.context_dashboard_label.config(text=health_bar)
                self.token_lbl.config(text=token_text)
            except Exception: pass
        
        self.root.after(0, refresh_labels)
        
    except Exception as e:
        sys_log("DASHBOARD", f"Enhanced dashboard update error: {e}")
