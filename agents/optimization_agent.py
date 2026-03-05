from typing import List, Dict, Any
from ortools.sat.python import cp_model
import sys
sys.path.append('..')
from config.config import Config

class OptimizationAgent:
    """Agent responsible for optimizing timetable efficiency"""
    
    def __init__(self):
        self.name = "OptimizationAgent"
        self.config = Config()
    
    def optimize_timetable(self, data: Dict) -> Dict:
        """Use constraint programming to generate optimal timetable"""
        model = cp_model.CpModel()
        
        divisions = data.get('divisions', [])
        subjects = data.get('subjects', [])
        rooms = data.get('rooms', [])
        faculty = data.get('faculty', [])
        timeslots = data.get('timeslots', [])
        
        if not all([divisions, subjects, rooms, faculty, timeslots]):
            return {'status': 'infeasible', 'reason': 'Missing required data', 'assignments': []}
        
        # Decision variables: assignment[d][s][r][f][t] = 1 if assigned
        assignments = {}
        for d in range(len(divisions)):
            for s in range(len(subjects)):
                for r in range(len(rooms)):
                    for f in range(len(faculty)):
                        for t in range(len(timeslots)):
                            assignments[(d, s, r, f, t)] = model.NewBoolVar(
                                f'assign_d{d}_s{s}_r{r}_f{f}_t{t}'
                            )
        
        # Constraint 1: Each division-subject pair must be scheduled for required hours
        for d in range(len(divisions)):
            for s in range(len(subjects)):
                hours_needed = subjects[s].get('hours_per_week', 1)
                model.Add(
                    sum(assignments[(d, s, r, f, t)] 
                        for r in range(len(rooms))
                        for f in range(len(faculty))
                        for t in range(len(timeslots))) == hours_needed
                )
        
        # Constraint 2: No faculty overlap
        for f in range(len(faculty)):
            for t in range(len(timeslots)):
                model.Add(
                    sum(assignments[(d, s, r, f, t)]
                        for d in range(len(divisions))
                        for s in range(len(subjects))
                        for r in range(len(rooms))) <= 1
                )
        
        # Constraint 3: No room overlap
        for r in range(len(rooms)):
            for t in range(len(timeslots)):
                model.Add(
                    sum(assignments[(d, s, r, f, t)]
                        for d in range(len(divisions))
                        for s in range(len(subjects))
                        for f in range(len(faculty))) <= 1
                )
        
        # Constraint 4: No division overlap
        for d in range(len(divisions)):
            for t in range(len(timeslots)):
                model.Add(
                    sum(assignments[(d, s, r, f, t)]
                        for s in range(len(subjects))
                        for r in range(len(rooms))
                        for f in range(len(faculty))) <= 1
                )
        
        # Constraint 5: Room capacity must accommodate students
        for d in range(len(divisions)):
            for r in range(len(rooms)):
                for t in range(len(timeslots)):
                    student_count = divisions[d].get('student_count', 0)
                    room_capacity = rooms[r].get('capacity', 0)
                    
                    if student_count > room_capacity:
                        # Prevent assignment if capacity insufficient
                        model.Add(
                            sum(assignments[(d, s, r, f, t)]
                                for s in range(len(subjects))
                                for f in range(len(faculty))) == 0
                        )
        
        # Constraint 6: Lab subjects must use lab rooms
        for s in range(len(subjects)):
            if subjects[s].get('is_lab', False):
                for r in range(len(rooms)):
                    if not rooms[r].get('is_lab', False):
                        # Prevent lab subjects in non-lab rooms
                        model.Add(
                            sum(assignments[(d, s, r, f, t)]
                                for d in range(len(divisions))
                                for f in range(len(faculty))
                                for t in range(len(timeslots))) == 0
                        )
        
        # Constraint 7: Limit consecutive classes per division
        for d in range(len(divisions)):
            for day in self.config.WORKING_DAYS:
                day_slots = [t for t in range(len(timeslots)) 
                           if timeslots[t].get('day') == day]
                
                for i in range(len(day_slots) - self.config.MAX_CONSECUTIVE_CLASSES + 1):
                    consecutive_slots = day_slots[i:i + self.config.MAX_CONSECUTIVE_CLASSES + 1]
                    model.Add(
                        sum(assignments[(d, s, r, f, t)]
                            for s in range(len(subjects))
                            for r in range(len(rooms))
                            for f in range(len(faculty))
                            for t in consecutive_slots) <= self.config.MAX_CONSECUTIVE_CLASSES
                    )
        
        # Objective: Minimize gaps and maximize room utilization efficiency
        gap_penalties = []
        utilization_bonuses = []
        
        # Minimize gaps in division schedules
        for d in range(len(divisions)):
            for day in self.config.WORKING_DAYS:
                day_slots = [t for t in range(len(timeslots)) 
                           if timeslots[t].get('day') == day]
                
                for i in range(len(day_slots) - 1):
                    current_slot = day_slots[i]
                    next_slot = day_slots[i + 1]
                    
                    # Gap variable: 1 if there's a gap between current and next slot
                    gap_var = model.NewBoolVar(f'gap_d{d}_day{day}_slot{i}')
                    
                    # Current slot has class
                    has_current = model.NewBoolVar(f'has_current_d{d}_slot{current_slot}')
                    model.Add(has_current == sum(assignments[(d, s, r, f, current_slot)]
                                               for s in range(len(subjects))
                                               for r in range(len(rooms))
                                               for f in range(len(faculty))))
                    
                    # Next slot has class
                    has_next = model.NewBoolVar(f'has_next_d{d}_slot{next_slot}')
                    model.Add(has_next == sum(assignments[(d, s, r, f, next_slot)]
                                            for s in range(len(subjects))
                                            for r in range(len(rooms))
                                            for f in range(len(faculty))))
                    
                    # Gap exists if current has class but next doesn't
                    model.Add(gap_var >= has_current - has_next)
                    model.Add(gap_var <= has_current)
                    model.Add(gap_var <= 1 - has_next)
                    
                    gap_penalties.append(gap_var)
        
        # Maximize room utilization
        for r in range(len(rooms)):
            room_usage = sum(assignments[(d, s, r, f, t)]
                           for d in range(len(divisions))
                           for s in range(len(subjects))
                           for f in range(len(faculty))
                           for t in range(len(timeslots)))
            utilization_bonuses.append(room_usage)
        
        # Combined objective: minimize gaps, maximize utilization
        model.Minimize(sum(gap_penalties) - sum(utilization_bonuses) // 10)
        
        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.SOLVER_TIMEOUT_SECONDS
        status = solver.Solve(model)
        
        result = {
            'status': 'optimal' if status == cp_model.OPTIMAL else 
                     'feasible' if status == cp_model.FEASIBLE else 'infeasible',
            'assignments': [],
            'solver_stats': {
                'solve_time': solver.WallTime(),
                'objective_value': solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None
            }
        }
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            for (d, s, r, f, t), var in assignments.items():
                if solver.Value(var) == 1:
                    result['assignments'].append({
                        'division_id': divisions[d]['id'],
                        'subject_id': subjects[s]['id'],
                        'room_id': rooms[r]['id'],
                        'faculty_id': faculty[f]['id'],
                        'timeslot_id': timeslots[t]['id'],
                        'division_name': divisions[d].get('name', ''),
                        'subject_name': subjects[s].get('name', ''),
                        'room_number': rooms[r].get('room_number', ''),
                        'faculty_name': faculty[f].get('name', ''),
                        'day': timeslots[t].get('day', ''),
                        'start_time': str(timeslots[t].get('start_time', '')),
                        'end_time': str(timeslots[t].get('end_time', ''))
                    })
        
        return result
    
    def calculate_utilization(self, timetable: List[Dict]) -> Dict:
        """Calculate resource utilization metrics"""
        if not timetable:
            return {'slot_utilization': 0, 'room_utilization': {}, 'total_classes': 0}
        
        total_possible_slots = len(set(e['timeslot_id'] for e in timetable)) * \
                              len(set(e['room_id'] for e in timetable))
        used_slots = len(timetable)
        
        room_usage = {}
        faculty_usage = {}
        division_usage = {}
        
        for entry in timetable:
            room_id = entry['room_id']
            faculty_id = entry['faculty_id']
            division_id = entry['division_id']
            
            room_usage[room_id] = room_usage.get(room_id, 0) + 1
            faculty_usage[faculty_id] = faculty_usage.get(faculty_id, 0) + 1
            division_usage[division_id] = division_usage.get(division_id, 0) + 1
        
        return {
            'slot_utilization': used_slots / total_possible_slots if total_possible_slots > 0 else 0,
            'room_utilization': room_usage,
            'faculty_utilization': faculty_usage,
            'division_utilization': division_usage,
            'total_classes': used_slots,
            'average_room_usage': sum(room_usage.values()) / len(room_usage) if room_usage else 0,
            'average_faculty_load': sum(faculty_usage.values()) / len(faculty_usage) if faculty_usage else 0
        }
