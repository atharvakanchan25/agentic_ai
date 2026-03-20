"""
Validation Agent - Handles data validation and integrity checks
"""
from typing import Dict, Any, List
from datetime import datetime
import re

from .base_agent import BaseAgent

class ValidationAgent(BaseAgent):
    """Agent responsible for validating input data and ensuring data integrity"""
    
    def __init__(self):
        capabilities = [
            "validate_input_data",
            "check_data_completeness", 
            "verify_constraints",
            "validate_timetable_structure",
            "check_business_rules"
        ]
        super().__init__("ValidationAgent", capabilities)
        
        # Validation rules
        self.validation_rules = {
            "department": {
                "required_fields": ["name", "code"],
                "field_types": {"name": str, "code": str},
                "field_constraints": {
                    "code": {"pattern": r"^[A-Z]{2,5}$", "max_length": 5}
                }
            },
            "subject": {
                "required_fields": ["name", "code", "hours_per_week", "department_id"],
                "field_types": {"name": str, "code": str, "hours_per_week": int, "department_id": int, "is_lab": bool},
                "field_constraints": {
                    "hours_per_week": {"min": 1, "max": 10},
                    "code": {"pattern": r"^[A-Z]{2,8}[0-9]{3}$"}
                }
            },
            "room": {
                "required_fields": ["room_number", "capacity", "floor"],
                "field_types": {"room_number": str, "capacity": int, "floor": int, "is_lab": bool},
                "field_constraints": {
                    "capacity": {"min": 10, "max": 200},
                    "floor": {"min": 0, "max": 10}
                }
            },
            "faculty": {
                "required_fields": ["name", "employee_id", "department_id"],
                "field_types": {"name": str, "employee_id": str, "department_id": int},
                "field_constraints": {
                    "employee_id": {"pattern": r"^[A-Z]{2}[0-9]{4,6}$"}
                }
            },
            "division": {
                "required_fields": ["name", "year", "student_count", "department_id"],
                "field_types": {"name": str, "year": int, "student_count": int, "department_id": int},
                "field_constraints": {
                    "year": {"min": 1, "max": 4},
                    "student_count": {"min": 1, "max": 120}
                }
            },
            "timeslot": {
                "required_fields": ["day", "slot_number", "start_time", "end_time"],
                "field_types": {"day": str, "slot_number": int, "start_time": str, "end_time": str},
                "field_constraints": {
                    "day": {"allowed_values": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]},
                    "slot_number": {"min": 1, "max": 10}
                }
            }
        }
    
    async def _initialize_agent(self):
        """Initialize validation agent"""
        self.log_action("Validation agent initialized")
    
    def _register_custom_handlers(self):
        """Register custom MCP handlers"""
        if self.mcp_client:
            self.mcp_client.register_handler("validate_entity", self._handle_validate_entity)
            self.mcp_client.register_handler("batch_validate", self._handle_batch_validate)
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process validation requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        self.log_action(f"Processing validation request: {method}")
        
        if method == "validate_input_data":
            return await self.validate_input_data(params)
        elif method == "check_data_completeness":
            return await self.check_data_completeness(params)
        elif method == "verify_constraints":
            return await self.verify_constraints(params)
        elif method == "validate_timetable_structure":
            return await self.validate_timetable_structure(params)
        elif method == "check_business_rules":
            return await self.check_business_rules(params)
        else:
            return {"status": "error", "message": f"Unknown validation method: {method}"}
    
    async def validate_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data structure and content"""
        self.log_action("Starting comprehensive input data validation")
        
        validation_results = {
            "status": "valid",
            "errors": [],
            "warnings": [],
            "entity_results": {}
        }
        
        # Validate each entity type
        for entity_type in ["departments", "subjects", "rooms", "faculty", "divisions", "timeslots"]:
            if entity_type in data:
                entity_validation = await self._validate_entity_list(entity_type[:-1], data[entity_type])
                validation_results["entity_results"][entity_type] = entity_validation
                
                if entity_validation["errors"]:
                    validation_results["errors"].extend(entity_validation["errors"])
                if entity_validation["warnings"]:
                    validation_results["warnings"].extend(entity_validation["warnings"])
        
        # Set overall status
        if validation_results["errors"]:
            validation_results["status"] = "invalid"
        elif validation_results["warnings"]:
            validation_results["status"] = "valid_with_warnings"
        
        self.log_action(f"Input validation completed", {
            "status": validation_results["status"],
            "error_count": len(validation_results["errors"]),
            "warning_count": len(validation_results["warnings"])
        })
        
        return validation_results
    
    async def _validate_entity_list(self, entity_type: str, entities: List[Dict]) -> Dict[str, Any]:
        """Validate a list of entities of a specific type"""
        results = {
            "entity_type": entity_type,
            "total_count": len(entities),
            "valid_count": 0,
            "errors": [],
            "warnings": []
        }
        
        if entity_type not in self.validation_rules:
            results["errors"].append(f"No validation rules defined for entity type: {entity_type}")
            return results
        
        rules = self.validation_rules[entity_type]
        
        for i, entity in enumerate(entities):
            entity_errors = []
            entity_warnings = []
            
            # Check required fields
            for field in rules["required_fields"]:
                if field not in entity:
                    entity_errors.append(f"{entity_type}[{i}]: Missing required field '{field}'")
                elif entity[field] is None or entity[field] == "":
                    entity_errors.append(f"{entity_type}[{i}]: Field '{field}' cannot be empty")
            
            # Check field types
            for field, expected_type in rules["field_types"].items():
                if field in entity and entity[field] is not None:
                    if not isinstance(entity[field], expected_type):
                        entity_errors.append(f"{entity_type}[{i}]: Field '{field}' must be of type {expected_type.__name__}")
            
            # Check field constraints
            if "field_constraints" in rules:
                for field, constraints in rules["field_constraints"].items():
                    if field in entity and entity[field] is not None:
                        field_value = entity[field]
                        
                        # Pattern validation
                        if "pattern" in constraints:
                            if not re.match(constraints["pattern"], str(field_value)):
                                entity_errors.append(f"{entity_type}[{i}]: Field '{field}' does not match required pattern")
                        
                        # Range validation
                        if "min" in constraints and isinstance(field_value, (int, float)):
                            if field_value < constraints["min"]:
                                entity_errors.append(f"{entity_type}[{i}]: Field '{field}' must be >= {constraints['min']}")
                        
                        if "max" in constraints and isinstance(field_value, (int, float)):
                            if field_value > constraints["max"]:
                                entity_errors.append(f"{entity_type}[{i}]: Field '{field}' must be <= {constraints['max']}")
                        
                        # Length validation
                        if "max_length" in constraints and isinstance(field_value, str):
                            if len(field_value) > constraints["max_length"]:
                                entity_errors.append(f"{entity_type}[{i}]: Field '{field}' exceeds maximum length")
                        
                        # Allowed values validation
                        if "allowed_values" in constraints:
                            if field_value not in constraints["allowed_values"]:
                                entity_errors.append(f"{entity_type}[{i}]: Field '{field}' must be one of {constraints['allowed_values']}")
            
            # Add entity-specific validation
            entity_specific_errors = await self._validate_entity_specific(entity_type, entity, i)
            entity_errors.extend(entity_specific_errors)
            
            if not entity_errors:
                results["valid_count"] += 1
            else:
                results["errors"].extend(entity_errors)
        
        return results
    
    async def _validate_entity_specific(self, entity_type: str, entity: Dict, index: int) -> List[str]:
        """Entity-specific validation logic"""
        errors = []
        
        if entity_type == "subject":
            # Lab subjects should have more hours
            if entity.get("is_lab", False) and entity.get("hours_per_week", 0) < 2:
                errors.append(f"subject[{index}]: Lab subjects should have at least 2 hours per week")
        
        elif entity_type == "room":
            # Lab rooms should have higher capacity
            if entity.get("is_lab", False) and entity.get("capacity", 0) < 20:
                errors.append(f"room[{index}]: Lab rooms should have capacity of at least 20")
        
        elif entity_type == "timeslot":
            # Validate time format and logic
            start_time = entity.get("start_time", "")
            end_time = entity.get("end_time", "")
            
            if start_time and end_time:
                try:
                    start_hour = int(start_time.split(":")[0])
                    end_hour = int(end_time.split(":")[0])
                    
                    if start_hour >= end_hour:
                        errors.append(f"timeslot[{index}]: Start time must be before end time")
                    
                    if start_hour < 8 or end_hour > 18:
                        errors.append(f"timeslot[{index}]: Time slots should be between 8:00 and 18:00")
                        
                except (ValueError, IndexError):
                    errors.append(f"timeslot[{index}]: Invalid time format (use HH:MM)")
        
        return errors
    
    async def check_data_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if data is complete for timetable generation"""
        self.log_action("Checking data completeness")
        
        required_entities = ["departments", "subjects", "rooms", "divisions", "timeslots"]
        missing_entities = []
        insufficient_data = []
        
        for entity in required_entities:
            if entity not in data:
                missing_entities.append(entity)
            elif not data[entity] or len(data[entity]) == 0:
                insufficient_data.append(f"No {entity} defined")
        
        # Check minimum requirements
        if "subjects" in data and len(data["subjects"]) < 3:
            insufficient_data.append("At least 3 subjects required for meaningful timetable")
        
        if "rooms" in data and len(data["rooms"]) < 2:
            insufficient_data.append("At least 2 rooms required")
        
        if "timeslots" in data and len(data["timeslots"]) < 5:
            insufficient_data.append("At least 5 time slots required")
        
        status = "complete"
        if missing_entities:
            status = "incomplete"
        elif insufficient_data:
            status = "insufficient"
        
        return {
            "status": status,
            "missing_entities": missing_entities,
            "insufficient_data": insufficient_data,
            "completeness_score": self._calculate_completeness_score(data)
        }
    
    def _calculate_completeness_score(self, data: Dict[str, Any]) -> float:
        """Calculate completeness score (0-100)"""
        required_entities = ["departments", "subjects", "rooms", "faculty", "divisions", "timeslots"]
        score = 0
        
        for entity in required_entities:
            if entity in data and data[entity]:
                entity_score = min(len(data[entity]) / 5, 1.0) * (100 / len(required_entities))
                score += entity_score
        
        return round(score, 2)
    
    async def verify_constraints(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that constraints can be satisfied"""
        self.log_action("Verifying constraint satisfiability")
        
        constraint_issues = []
        
        divisions = data.get("divisions", [])
        rooms = data.get("rooms", [])
        subjects = data.get("subjects", [])
        timeslots = data.get("timeslots", [])
        
        # Check room capacity constraints
        for division in divisions:
            student_count = division.get("student_count", 0)
            suitable_rooms = [r for r in rooms if r.get("capacity", 0) >= student_count]
            
            if not suitable_rooms:
                constraint_issues.append({
                    "type": "capacity_constraint",
                    "message": f"No rooms with sufficient capacity for division {division.get('name')} ({student_count} students)"
                })
        
        # Check lab room constraints
        lab_subjects = [s for s in subjects if s.get("is_lab", False)]
        lab_rooms = [r for r in rooms if r.get("is_lab", False)]
        
        if lab_subjects and not lab_rooms:
            constraint_issues.append({
                "type": "lab_constraint",
                "message": "Lab subjects exist but no lab rooms available"
            })
        
        # Check time slot sufficiency
        total_hours_needed = 0
        for division in divisions:
            for subject in subjects:
                total_hours_needed += subject.get("hours_per_week", 0)
        
        available_slots = len(timeslots)
        if total_hours_needed > available_slots:
            constraint_issues.append({
                "type": "time_constraint",
                "message": f"Insufficient time slots: need {total_hours_needed}, have {available_slots}"
            })
        
        return {
            "status": "satisfiable" if not constraint_issues else "unsatisfiable",
            "constraint_issues": constraint_issues,
            "total_issues": len(constraint_issues)
        }
    
    async def validate_timetable_structure(self, timetable: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the structure of a generated timetable"""
        self.log_action("Validating timetable structure")
        
        required_fields = ["division_id", "subject_id", "room_id", "timeslot_id", "day", "slot_number"]
        structural_errors = []
        
        for i, entry in enumerate(timetable):
            for field in required_fields:
                if field not in entry:
                    structural_errors.append(f"Entry {i}: Missing field '{field}'")
                elif entry[field] is None:
                    structural_errors.append(f"Entry {i}: Field '{field}' cannot be null")
        
        return {
            "status": "valid" if not structural_errors else "invalid",
            "structural_errors": structural_errors,
            "total_entries": len(timetable),
            "valid_entries": len(timetable) - len(structural_errors)
        }
    
    async def check_business_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check business rules and best practices"""
        self.log_action("Checking business rules")

        rule_violations = []
        warnings = []

        divisions = data.get("divisions", [])
        subjects  = data.get("subjects", [])
        timeslots = data.get("timeslots", [])
        faculty   = data.get("faculty", [])

        # ── Rule 1: No more than 6 hours per day per division ─────────────────
        days = list({ts["day"] for ts in timeslots})
        for division in divisions:
            total_hours = sum(s.get("hours_per_week", 0) for s in subjects)
            if days:
                avg_per_day = total_hours / len(days)
                if avg_per_day > 6:
                    rule_violations.append({
                        "rule": "max_hours_per_day",
                        "message": (
                            f"Division '{division.get('name')}' requires ~{avg_per_day:.1f} hours/day "
                            f"({total_hours} total over {len(days)} days) — exceeds 6-hour limit."
                        )
                    })

        # ── Rule 2: Lab subjects must have at least 2 consecutive slots available ─
        lab_subjects = [s for s in subjects if s.get("is_lab", False)]
        if lab_subjects:
            day_slot_map: Dict[str, List[int]] = {}
            for ts in timeslots:
                day_slot_map.setdefault(ts["day"], []).append(ts["slot_number"])

            has_consecutive = any(
                any(
                    slot + 1 in slots
                    for slot in slots
                )
                for slots in day_slot_map.values()
            )
            if not has_consecutive:
                rule_violations.append({
                    "rule": "lab_consecutive_slots",
                    "message": (
                        f"{len(lab_subjects)} lab subject(s) exist but no two consecutive "
                        "time slots are available on any day."
                    )
                })

        # ── Rule 3: Faculty workload balance ──────────────────────────────────
        if faculty and subjects:
            dept_faculty_count: Dict[int, int] = {}
            dept_subject_hours: Dict[int, int] = {}
            for f in faculty:
                dept_id = f.get("department_id")
                dept_faculty_count[dept_id] = dept_faculty_count.get(dept_id, 0) + 1
            for s in subjects:
                dept_id = s.get("department_id")
                dept_subject_hours[dept_id] = (
                    dept_subject_hours.get(dept_id, 0) + s.get("hours_per_week", 0)
                )

            for dept_id, hours in dept_subject_hours.items():
                fcount = dept_faculty_count.get(dept_id, 0)
                if fcount == 0:
                    warnings.append(
                        f"Department {dept_id} has {hours} subject hours but no faculty assigned."
                    )
                elif hours / fcount > 20:
                    warnings.append(
                        f"Department {dept_id}: avg faculty load is {hours/fcount:.1f} hrs/week — consider adding more faculty."
                    )

        return {
            "status": "compliant" if not rule_violations else "violations_found",
            "rule_violations": rule_violations,
            "warnings": warnings
        }
    
    async def _handle_validate_entity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle single entity validation via MCP"""
        entity_type = params.get("entity_type")
        entity_data = params.get("entity_data")
        
        if not entity_type or not entity_data:
            return {"status": "error", "message": "Missing entity_type or entity_data"}
        
        return await self._validate_entity_list(entity_type, [entity_data])
    
    async def _handle_batch_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch validation via MCP"""
        return await self.validate_input_data(params)
    
    async def _cleanup_agent(self):
        """Cleanup validation agent"""
        self.log_action("Validation agent cleanup completed")