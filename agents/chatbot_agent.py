
        
        intent = self._detect_intent(user_message)
        response = self._generate_response(intent, user_message)
        
        self.conversation_history.append({"role": "assistant", "message": response['message']})
        return response
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        if any(word in message for word in ['add', 'create', 'new']):
            if 'department' in message:
                return 'add_department'
            elif 'subject' in message or 'course' in message:
                return 'add_subject'
            elif 'room' in message or 'classroom' in message:
                return 'add_room'
            elif 'faculty' in message or 'teacher' in message or 'professor' in message:
                return 'add_faculty'
            elif 'division' in message or 'class' in message:
                return 'add_division'
        
        if any(word in message for word in ['generate', 'create', 'make']) and 'timetable' in message:
            return 'generate_timetable'
        
        if any(word in message for word in ['change', 'modify', 'update', 'alter']):
            return 'modify_timetable'
        
        if any(word in message for word in ['show', 'display', 'view', 'see']):
            return 'view_data'
        
        if any(word in message for word in ['delete', 'remove']):
            return 'delete_data'
        
        if any(word in message for word in ['help', 'what can you do', 'commands']):
            return 'help'
        
        return 'unknown'
    
    def _generate_response(self, intent: str, message: str) -> Dict[str, Any]:
        """Generate response based on intent"""
        
        if intent == 'add_department':
            return {
                'message': 'I can help you add a department. Please provide the department name and code.',
                'action': 'request_department_info',
                'next_step': 'collect_department_data'
            }
        
        elif intent == 'add_subject':
            return {
                'message': 'I can help you add a subject. Please provide: subject name, code, hours per week, and whether it is a lab subject.',
                'action': 'request_subject_info',
                'next_step': 'collect_subject_data'
            }
        
        elif intent == 'add_room':
            return {
                'message': 'I can help you add a room. Please provide: room number, floor, capacity, bench count, and whether it is a lab.',
                'action': 'request_room_info',
                'next_step': 'collect_room_data'
            }
        
        elif intent == 'add_faculty':
            return {
                'message': 'I can help you add a faculty member. Please provide: name and employee ID.',
                'action': 'request_faculty_info',
                'next_step': 'collect_faculty_data'
            }
        
        elif intent == 'add_division':
            return {
                'message': 'I can help you add a division. Please provide: division name, year, and student count.',
                'action': 'request_division_info',
                'next_step': 'collect_division_data'
            }
        
        elif intent == 'generate_timetable':
            return {
                'message': 'I will generate the timetable for you. Please confirm that all data has been entered.',
                'action': 'generate_timetable',
                'next_step': 'confirm_generation'
            }
        
        elif intent == 'modify_timetable':
            return {
                'message': 'I can help you modify the timetable. What would you like to change?',
                'action': 'request_modification',
                'next_step': 'collect_modification_details'
            }
        
        elif intent == 'view_data':
            return {
                'message': 'What would you like to view? (departments, subjects, rooms, faculty, divisions, or timetable)',
                'action': 'request_view_type',
                'next_step': 'display_data'
            }
        
        elif intent == 'delete_data':
            return {
                'message': 'What would you like to delete? Please specify the type and details.',
                'action': 'request_delete_info',
                'next_step': 'confirm_deletion'
            }
        
        elif intent == 'help':
            return {
                'message': '''I can help you with:
- Add departments, subjects, rooms, faculty, and divisions
- Generate timetables
- Modify existing timetables
- View current data
- Delete data

Try saying things like:
"Add a new department"
"Generate timetable"
"Show me all subjects"
"Change room for CS-A"''',
                'action': 'show_help',
                'next_step': None
            }
        
        else:
            return {
                'message': 'I am not sure what you mean. Try asking me to add data, generate a timetable, or type "help" for more options.',
                'action': 'clarify',
                'next_step': None
            }
    
    def extract_data_from_message(self, message: str, data_type: str) -> Dict[str, Any]:
        """Extract structured data from natural language"""
        data = {}
        
        if data_type == 'department':
            name_match = re.search(r'name[:\s]+([a-zA-Z\s]+?)(?:,|code|$)', message, re.IGNORECASE)
            code_match = re.search(r'code[:\s]+([A-Z]+)', message, re.IGNORECASE)
            
            if name_match:
                data['name'] = name_match.group(1).strip()
            if code_match:
                data['code'] = code_match.group(1).strip()
        
        elif data_type == 'subject':
            name_match = re.search(r'name[:\s]+([a-zA-Z\s]+?)(?:,|code|hours|$)', message, re.IGNORECASE)
            code_match = re.search(r'code[:\s]+([A-Z0-9]+)', message, re.IGNORECASE)
            hours_match = re.search(r'(\d+)\s*hours?', message, re.IGNORECASE)
            is_lab = 'lab' in message.lower()
            
            if name_match:
                data['name'] = name_match.group(1).strip()
            if code_match:
                data['code'] = code_match.group(1).strip()
            if hours_match:
                data['hours_per_week'] = int(hours_match.group(1))
            data['is_lab'] = is_lab
        
        elif data_type == 'room':
            room_match = re.search(r'room\s*(?:number)?\s*[:\s]*([0-9A-Z]+)', message, re.IGNORECASE)
            floor_match = re.search(r'floor[:\s]+(\d+)', message, re.IGNORECASE)
            capacity_match = re.search(r'capacity[:\s]+(\d+)', message, re.IGNORECASE)
            bench_match = re.search(r'bench(?:es)?[:\s]+(\d+)', message, re.IGNORECASE)
            is_lab = 'lab' in message.lower()
            
            if room_match:
                data['room_number'] = room_match.group(1).strip()
            if floor_match:
                data['floor'] = int(floor_match.group(1))
            if capacity_match:
                data['capacity'] = int(capacity_match.group(1))
            if bench_match:
                data['bench_count'] = int(bench_match.group(1))
            data['is_lab'] = is_lab
            data['room_type'] = 'Lab' if is_lab else 'Classroom'
        
        return data
    
    def get_suggestions(self, partial_message: str) -> List[str]:
        """Provide autocomplete suggestions"""
        suggestions = [
            "Add a new department",
            "Add a new subject",
            "Add a new room",
            "Add faculty member",
            "Add student division",
            "Generate timetable",
            "Show all departments",
            "Show all subjects",
            "Modify timetable",
            "Help"
        ]
        
        if not partial_message:
            return suggestions[:5]
        
        partial_lower = partial_message.lower()
        return [s for s in suggestions if partial_lower in s.lower()][:5]
