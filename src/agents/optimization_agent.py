"""
Optimization Agent - Handles timetable optimization using constraint programming
"""
from typing import Dict, Any, List, Tuple, Optional
import time
from datetime import datetime
from ortools.sat.python import cp_model
import numpy as np

from .base_agent import BaseAgent

class OptimizationAgent(BaseAgent):
    """Agent responsible for generating optimal timetables using constraint programming"""
    
    def __init__(self):
        capabilities = [
            "optimize_timetable",
            "calculate_utilization",
            "optimize_with_preferences",
            "generate_multiple_solutions",
            "evaluate_solution_quality"
        ]
        super().__init__("OptimizationAgent", capabilities)
        
        # Optimization parameters
        self.max_solve_time = 60  # seconds
        self.solution_limit = 1
        self.optimization_objectives = {
            "minimize_room_changes": 1.0,
            "balance_daily_load": 1.0,
            "minimize_gaps": 1.0,
            "maximize_room_utilization": 0.5
        }
    
    async def _initialize_agent(self):
        """Initialize optimization agent"""
        self.log_action("Optimization agent initialized with OR-Tools CP-SAT solver")
    
    def _register_custom_handlers(self):
        """Register custom MCP handlers"""
        if self.mcp_client:
            self.mcp_client.register_handler("set_optimization_params", self._handle_set_params)
            self.mcp_client.register_handler("get_solver_stats", self._handle_get_solver_stats)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process optimization requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        self.log_action(f"Processing optimization request: {method}")
        
        if method == "optimize_timetable":
            return await self.optimize_timetable(params)
        elif method == "calculate_utilization":
            return await self.calculate_utilization(params)
        elif method == "optimize_with_preferences":
            return await self.optimize_with_preferences(params)
        elif method == "generate_multiple_solutions":
            return await self.generate_multiple_solutions(params)
        elif method == "evaluate_solution_quality":
            return await self.evaluate_solution_quality(params)
        else:
            return {"status": "error", "message": f"Unknown optimization method: {method}"}
    
    async def optimize_timetable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimal timetable using constraint programming"""
        self.log_action("Starting timetable optimization")
        start_time = time.time()
        
        try:
            # Extract and validate data
            divisions = data.get("divisions", [])
            subjects = data.get("subjects", [])
            rooms = data.get("rooms", [])
            timeslots = data.get("timeslots", [])
            faculty = data.get("faculty", [])
            
            if not all([divisions, subjects, rooms, timeslots]):
                return {
                    "status": "error",
                    "message": "Missing required data for optimization",
                    "required": ["divisions", "subjects", "rooms", "timeslots"]
                }
            
            # Create optimization model
            model = cp_model.CpModel()
            
            # Create indices
            D = len(divisions)  # divisions
            S = len(subjects)   # subjects
            R = len(rooms)      # rooms
            T = len(timeslots)  # timeslots
            
            self.log_action(f"Creating model with {D} divisions, {S} subjects, {R} rooms, {T} timeslots")
            
            # Decision variables
            # x[d][s][r][t] = 1 if division d has subject s in room r at time t
            x = {}
            for d in range(D):
                for s in range(S):
                    for r in range(R):
                        for t in range(T):
                            x[(d, s, r, t)] = model.NewBoolVar(f'x_{d}_{s}_{r}_{t}')
            
            # Auxiliary variables for optimization objectives
            room_changes = {}  # Track room changes for divisions
            daily_load = {}    # Track daily load per division
            gaps = {}          # Track gaps in schedule
            
            # CONSTRAINTS
            
            # 1. Each division-subject pair must be scheduled exactly for required hours
            for d in range(D):
                for s in range(S):
                    hours_needed = subjects[s].get("hours_per_week", 1)
                    model.Add(
                        sum(x[(d, s, r, t)] for r in range(R) for t in range(T)) == hours_needed
                    )
            
            # 2. No room can be used by multiple divisions at the same time
            for r in range(R):
                for t in range(T):
                    model.Add(
                        sum(x[(d, s, r, t)] for d in range(D) for s in range(S)) <= 1
                    )
            
            # 3. No division can have multiple subjects at the same time
            for d in range(D):
                for t in range(T):
                    model.Add(
                        sum(x[(d, s, r, t)] for s in range(S) for r in range(R)) <= 1
                    )
            
            # 4. Room capacity constraints
            for d in range(D):
                for s in range(S):
                    for r in range(R):
                        for t in range(T):
                            student_count = divisions[d].get("student_count", 0)
                            room_capacity = rooms[r].get("capacity", 0)
                            if student_count > room_capacity:
                                model.Add(x[(d, s, r, t)] == 0)
            
            # 5. Lab subjects must be assigned to lab rooms
            for d in range(D):
                for s in range(S):
                    if subjects[s].get("is_lab", False):
                        for r in range(R):
                            if not rooms[r].get("is_lab", False):
                                for t in range(T):
                                    model.Add(x[(d, s, r, t)] == 0)
            
            # 6. Faculty constraints (if faculty data is available)
            if faculty:
                faculty_assignments = self._add_faculty_constraints(model, x, data, D, S, R, T)
            
            # 7. Time-based constraints
            self._add_time_constraints(model, x, timeslots, D, S, R, T)
            
            # 8. Soft constraints for optimization
            objective_terms = []
            
            # Minimize room changes for each division
            for d in range(D):
                room_change_vars = []
                for t1 in range(T-1):
                    for t2 in range(t1+1, T):
                        # Check if division d is in different rooms at consecutive times
                        for r1 in range(R):
                            for r2 in range(R):
                                if r1 != r2:
                                    change_var = model.NewBoolVar(f'room_change_{d}_{t1}_{t2}_{r1}_{r2}')
                                    # If division d is in room r1 at time t1 and room r2 at time t2
                                    model.AddImplication(
                                        sum(x[(d, s, r1, t1)] for s in range(S)),
                                        change_var
                                    ).OnlyEnforceIf(sum(x[(d, s, r2, t2)] for s in range(S)))
                                    room_change_vars.append(change_var)
                
                if room_change_vars:
                    objective_terms.append(
                        sum(room_change_vars) * self.optimization_objectives["minimize_room_changes"]
                    )
            
            # Balance daily load
            days = list(set(ts.get("day") for ts in timeslots))
            for d in range(D):
                daily_loads = []
                for day in days:
                    day_slots = [i for i, ts in enumerate(timeslots) if ts.get("day") == day]
                    if day_slots:
                        daily_load = sum(
                            x[(d, s, r, t)] 
                            for s in range(S) 
                            for r in range(R) 
                            for t in day_slots
                        )
                        daily_loads.append(daily_load)
                
                if len(daily_loads) > 1:
                    # Minimize variance in daily loads
                    max_daily = model.NewIntVar(0, len(timeslots), f'max_daily_{d}')
                    min_daily = model.NewIntVar(0, len(timeslots), f'min_daily_{d}')
                    
                    for load in daily_loads:
                        model.Add(max_daily >= load)
                        model.Add(min_daily <= load)
                    
                    objective_terms.append(
                        (max_daily - min_daily) * self.optimization_objectives["balance_daily_load"]
                    )
            
            # Set objective
            if objective_terms:
                model.Minimize(sum(objective_terms))
            
            # Solve the model
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = self.max_solve_time
            solver.parameters.log_search_progress = False
            
            self.log_action("Solving constraint model")
            status = solver.Solve(model)
            
            solve_time = time.time() - start_time
            
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                # Extract solution
                timetable = []
                for d in range(D):
                    for s in range(S):
                        for r in range(R):
                            for t in range(T):
                                if solver.Value(x[(d, s, r, t)]) == 1:
                                    timetable.append({
                                        "division_id": divisions[d].get("id"),
                                        "division_name": divisions[d].get("name"),
                                        "subject_id": subjects[s].get("id"),
                                        "subject_name": subjects[s].get("name"),
                                        "subject_code": subjects[s].get("code"),
                                        "room_id": rooms[r].get("id"),
                                        "room_number": rooms[r].get("room_number"),
                                        "timeslot_id": timeslots[t].get("id"),
                                        "day": timeslots[t].get("day"),
                                        "slot_number": timeslots[t].get("slot_number"),
                                        "start_time": timeslots[t].get("start_time"),
                                        "end_time": timeslots[t].get("end_time"),
                                        "is_lab": subjects[s].get("is_lab", False)
                                    })
                
                # Calculate solution quality metrics
                quality_metrics = await self._calculate_solution_quality(timetable, data)
                
                self.log_action(f"Optimization completed successfully", {
                    "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                    "assignments": len(timetable),
                    "solve_time": solve_time,
                    "objective_value": solver.ObjectiveValue() if objective_terms else 0
                })
                
                return {
                    "status": "success",
                    "solver_status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                    "timetable": timetable,
                    "solve_time": solve_time,
                    "objective_value": solver.ObjectiveValue() if objective_terms else 0,
                    "quality_metrics": quality_metrics,
                    "statistics": {
                        "total_assignments": len(timetable),
                        "solver_iterations": solver.NumBranches(),
                        "solver_conflicts": solver.NumConflicts()
                    }
                }
            
            else:
                self.log_action(f"Optimization failed", {
                    "solver_status": solver.StatusName(status),
                    "solve_time": solve_time
                })
                
                return {
                    "status": "failed",
                    "solver_status": solver.StatusName(status),
                    "message": f"No feasible solution found: {solver.StatusName(status)}",
                    "solve_time": solve_time,
                    "suggestions": self._get_infeasibility_suggestions(data)
                }
        
        except Exception as e:
            self.log_action(f"Optimization error: {str(e)}")
            return {
                "status": "error",
                "message": f"Optimization failed: {str(e)}",
                "solve_time": time.time() - start_time
            }
    
    def _add_faculty_constraints(self, model, x, data, D, S, R, T):
        """Add faculty-related constraints"""
        faculty = data.get("faculty", [])
        subject_faculty_map = {}  # Map subjects to faculty
        
        # Simple mapping: assume each subject is taught by one faculty member
        for i, subject in enumerate(data.get("subjects", [])):
            dept_id = subject.get("department_id")
            dept_faculty = [f for f in faculty if f.get("department_id") == dept_id]
            if dept_faculty:
                subject_faculty_map[i] = dept_faculty[0].get("id")
        
        # Faculty cannot teach multiple classes at the same time
        faculty_time_constraints = {}
        for s in range(S):
            if s in subject_faculty_map:
                faculty_id = subject_faculty_map[s]
                if faculty_id not in faculty_time_constraints:
                    faculty_time_constraints[faculty_id] = []
                
                for d in range(D):
                    for r in range(R):
                        for t in range(T):
                            faculty_time_constraints[faculty_id].append(x[(d, s, r, t)])
        
        # Add constraints
        for faculty_id, assignments in faculty_time_constraints.items():
            for t in range(T):
                time_assignments = [
                    x[(d, s, r, t)] 
                    for d in range(D) 
                    for s in range(S) 
                    for r in range(R)
                    if s in subject_faculty_map and subject_faculty_map[s] == faculty_id
                ]
                if time_assignments:
                    model.Add(sum(time_assignments) <= 1)
        
        return subject_faculty_map
    
    def _add_time_constraints(self, model, x, timeslots, D, S, R, T):
        """Add time-based constraints"""
        # Group timeslots by day
        day_slots = {}
        for i, ts in enumerate(timeslots):
            day = ts.get("day")
            if day not in day_slots:
                day_slots[day] = []
            day_slots[day].append(i)
        
        # Constraint: No more than 6 hours per day per division
        for d in range(D):
            for day, slots in day_slots.items():
                if len(slots) > 6:  # If more than 6 slots available in a day
                    model.Add(
                        sum(x[(d, s, r, t)] for s in range(S) for r in range(R) for t in slots) <= 6
                    )
        
        # Constraint: Lab sessions should be consecutive (if possible)
        for d in range(D):
            for s in range(S):
                if len(timeslots) > 0 and timeslots[0].get("is_lab", False):
                    # Try to schedule consecutive slots for lab subjects
                    for day, slots in day_slots.items():
                        if len(slots) >= 2:
                            for i in range(len(slots) - 1):
                                t1, t2 = slots[i], slots[i + 1]
                                # If scheduled in t1, prefer t2 as well
                                lab_t1 = sum(x[(d, s, r, t1)] for r in range(R))
                                lab_t2 = sum(x[(d, s, r, t2)] for r in range(R))
                                
                                # Soft constraint: encourage consecutive scheduling
                                # This would be handled in the objective function
    
    async def _calculate_solution_quality(self, timetable: List[Dict], data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for the solution"""
        if not timetable:
            return {"overall_score": 0, "metrics": {}}
        
        metrics = {}
        
        # Room utilization
        room_usage = {}
        for entry in timetable:
            room_id = entry.get("room_id")
            room_usage[room_id] = room_usage.get(room_id, 0) + 1
        
        total_slots = len(set(f"{e.get('day')}_{e.get('slot_number')}" for e in timetable))
        total_rooms = len(set(e.get("room_id") for e in timetable))
        max_possible_usage = total_rooms * total_slots
        actual_usage = sum(room_usage.values())
        
        metrics["room_utilization"] = (actual_usage / max_possible_usage * 100) if max_possible_usage > 0 else 0
        
        # Daily balance
        daily_distribution = {}
        for entry in timetable:
            day = entry.get("day")
            division_id = entry.get("division_id")
            key = f"{division_id}_{day}"
            daily_distribution[key] = daily_distribution.get(key, 0) + 1
        
        if daily_distribution:
            daily_values = list(daily_distribution.values())
            daily_variance = np.var(daily_values) if len(daily_values) > 1 else 0
            metrics["daily_balance_score"] = max(0, 100 - daily_variance * 10)
        else:
            metrics["daily_balance_score"] = 0
        
        # Gap analysis
        division_schedules = {}
        for entry in timetable:
            div_id = entry.get("division_id")
            day = entry.get("day")
            slot = entry.get("slot_number")
            
            if div_id not in division_schedules:
                division_schedules[div_id] = {}
            if day not in division_schedules[div_id]:
                division_schedules[div_id][day] = []
            
            division_schedules[div_id][day].append(slot)
        
        total_gaps = 0
        for div_id, days in division_schedules.items():
            for day, slots in days.items():
                if len(slots) > 1:
                    sorted_slots = sorted(slots)
                    for i in range(len(sorted_slots) - 1):
                        gap = sorted_slots[i + 1] - sorted_slots[i] - 1
                        total_gaps += max(0, gap)
        
        metrics["gap_score"] = max(0, 100 - total_gaps * 5)
        
        # Overall score
        weights = {"room_utilization": 0.3, "daily_balance_score": 0.4, "gap_score": 0.3}
        overall_score = sum(metrics[key] * weights[key] for key in weights if key in metrics)
        
        return {
            "overall_score": round(overall_score, 2),
            "metrics": metrics
        }
    
    def _get_infeasibility_suggestions(self, data: Dict[str, Any]) -> List[str]:
        """Provide suggestions when no feasible solution is found"""
        suggestions = []
        
        divisions = data.get("divisions", [])
        subjects = data.get("subjects", [])
        rooms = data.get("rooms", [])
        timeslots = data.get("timeslots", [])
        
        # Check basic feasibility issues
        total_hours_needed = sum(s.get("hours_per_week", 0) for s in subjects) * len(divisions)
        available_slots = len(timeslots)
        
        if total_hours_needed > available_slots:
            suggestions.append(f"Add more time slots: need {total_hours_needed}, have {available_slots}")
        
        # Check room capacity issues
        max_students = max((d.get("student_count", 0) for d in divisions), default=0)
        max_room_capacity = max((r.get("capacity", 0) for r in rooms), default=0)
        
        if max_students > max_room_capacity:
            suggestions.append("Add rooms with higher capacity or reduce division sizes")
        
        # Check lab room availability
        lab_subjects = [s for s in subjects if s.get("is_lab", False)]
        lab_rooms = [r for r in rooms if r.get("is_lab", False)]
        
        if lab_subjects and not lab_rooms:
            suggestions.append("Add lab rooms for lab subjects")
        
        return suggestions
    
    async def calculate_utilization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed utilization metrics"""
        timetable = data.get("timetable", [])
        
        if not timetable:
            return {"status": "error", "message": "No timetable data provided"}
        
        # Room utilization
        room_stats = {}
        for entry in timetable:
            room_id = entry.get("room_id")
            if room_id not in room_stats:
                room_stats[room_id] = {
                    "room_number": entry.get("room_number"),
                    "usage_count": 0,
                    "subjects": set(),
                    "divisions": set()
                }
            
            room_stats[room_id]["usage_count"] += 1
            room_stats[room_id]["subjects"].add(entry.get("subject_name"))
            room_stats[room_id]["divisions"].add(entry.get("division_name"))
        
        # Convert sets to lists for JSON serialization
        for room_id in room_stats:
            room_stats[room_id]["subjects"] = list(room_stats[room_id]["subjects"])
            room_stats[room_id]["divisions"] = list(room_stats[room_id]["divisions"])
        
        # Time slot utilization
        timeslot_stats = {}
        for entry in timetable:
            time_key = f"{entry.get('day')}_{entry.get('slot_number')}"
            if time_key not in timeslot_stats:
                timeslot_stats[time_key] = {
                    "day": entry.get("day"),
                    "slot_number": entry.get("slot_number"),
                    "usage_count": 0
                }
            timeslot_stats[time_key]["usage_count"] += 1
        
        # Overall metrics
        total_assignments = len(timetable)
        unique_rooms = len(room_stats)
        unique_timeslots = len(timeslot_stats)
        
        return {
            "status": "success",
            "overall_metrics": {
                "total_assignments": total_assignments,
                "unique_rooms_used": unique_rooms,
                "unique_timeslots_used": unique_timeslots,
                "average_room_utilization": total_assignments / unique_rooms if unique_rooms > 0 else 0,
                "average_timeslot_utilization": total_assignments / unique_timeslots if unique_timeslots > 0 else 0
            },
            "room_utilization": room_stats,
            "timeslot_utilization": timeslot_stats
        }
    
    async def _handle_set_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle optimization parameter updates via MCP"""
        if "max_solve_time" in params:
            self.max_solve_time = params["max_solve_time"]
        
        if "objectives" in params:
            self.optimization_objectives.update(params["objectives"])
        
        return {"status": "success", "message": "Parameters updated"}
    
    async def _handle_get_solver_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solver statistics request via MCP"""
        return {
            "max_solve_time": self.max_solve_time,
            "optimization_objectives": self.optimization_objectives,
            "solution_limit": self.solution_limit
        }
    
    async def _cleanup_agent(self):
        """Cleanup optimization agent"""
        self.log_action("Optimization agent cleanup completed")